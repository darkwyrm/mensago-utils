import argparse
from base64 import b85encode
import diceware
from glob import glob
import hashlib
import os.path
import platform
import shutil
import sys
import time
import uuid

import psycopg2
import nacl.public
import nacl.signing
import toml


from pycryptostring import CryptoString
from pymensago.encryption import EncryptionPair, Password, PublicKey, SigningPair
import pymensago.keycard as keycard
import pymensago.iscmds as iscmds
import pymensago.serverconn as serverconn

def load_server_config_file() -> dict:
	'''Loads the Mensago server configuration from the config file'''
	
	config_file_path = '/etc/mensagod/serverconfig.toml'
	if platform.system() == 'Windows':
		config_file_path = 'C:\\ProgramData\\mensagod\\serverconfig.toml'

	if os.path.exists(config_file_path):
		try:
			serverconfig = toml.load(config_file_path)
		except Exception as e:
			print("Unable to load server config %s: %s" % (config_file_path, e))
			sys.exit(1)
	else:
		serverconfig = {}
	
	serverconfig.setdefault('database', dict())
	serverconfig['database'].setdefault('engine','postgresql')
	serverconfig['database'].setdefault('ip','127.0.0.1')
	serverconfig['database'].setdefault('port','5432')
	serverconfig['database'].setdefault('name','mensago')
	serverconfig['database'].setdefault('user','mensago')
	serverconfig['database'].setdefault('password','CHANGEME')

	serverconfig.setdefault('network', dict())
	serverconfig['network'].setdefault('listen_ip','127.0.0.1')
	serverconfig['network'].setdefault('port','2001')

	serverconfig.setdefault('global', dict())

	serverconfig['global'].setdefault('domain', 'example.com')
	if platform.system() == 'Windows':
		serverconfig['global'].setdefault('top_dir','C:\\ProgramData\\mensago')
		serverconfig['global'].setdefault('workspace_dir','C:\\ProgramData\\mensago\\wsp')
	else:
		serverconfig['global'].setdefault('top_dir','/var/mensago')
		serverconfig['global'].setdefault('workspace_dir','/var/mensago/wsp')
	serverconfig['global'].setdefault('registration','private')
	serverconfig['global'].setdefault('default_quota',0)

	serverconfig.setdefault('security', dict())
	serverconfig['security'].setdefault('failure_delay_sec',3)
	serverconfig['security'].setdefault('max_failures',5)
	serverconfig['security'].setdefault('lockout_delay_min',15)
	serverconfig['security'].setdefault('registration_delay_min',15)

	if serverconfig['database']['engine'].lower() != 'postgresql':
		print("This script exepects a server config using PostgreSQL. Exiting")
		sys.exit()
	
	return serverconfig


def reset() -> dict:
	'''Resets the server database and workspace directory'''
	
	serverconfig = load_server_config_file()

	# Reset the test database to defaults
	try:
		conn = psycopg2.connect(host=serverconfig['database']['ip'],
								port=serverconfig['database']['port'],
								database=serverconfig['database']['name'],
								user=serverconfig['database']['user'],
								password=serverconfig['database']['password'])
	except Exception as e:
		print("Couldn't connect to database: %s" % e)
		sys.exit(1)

	empty_database(conn)
	out = populate_database(conn, serverconfig)
	reset_top_dir(serverconfig)

	return out


def empty_database(conn):
	'''Drops all tables from the database and creates new ones in their place.'''
	cur = conn.cursor()

	dropcmd = '''DO $$ DECLARE
		r RECORD;
	BEGIN
		FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = current_schema()) LOOP
			EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
		END LOOP;
	END $$;'''
	cur.execute(dropcmd)

	cur.execute("SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON "
				"n.oid = c.relnamespace WHERE n.nspname = 'public' AND c.relname = 'workspaces' AND "
				"c.relkind = 'r');")
	rows = cur.fetchall()
	if rows[0][0] is False:
		cur.execute("CREATE TABLE workspaces(rowid SERIAL PRIMARY KEY, wid CHAR(36) NOT NULL, "
			"uid VARCHAR(64), domain VARCHAR(255) NOT NULL, wtype VARCHAR(32) NOT NULL, "
			"status VARCHAR(16) NOT NULL, password VARCHAR(128));")


	cur.execute("SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON "
				"n.oid = c.relnamespace WHERE n.nspname = 'public' AND c.relname = 'aliases' AND "
				"c.relkind = 'r');")
	rows = cur.fetchall()
	if rows[0][0] is False:
		cur.execute("CREATE TABLE aliases(rowid SERIAL PRIMARY KEY, wid CHAR(36) NOT NULL, "
			"alias CHAR(292) NOT NULL);")


	cur.execute("SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON "
				"n.oid = c.relnamespace WHERE n.nspname = 'public' AND c.relname = 'iwkspc_folders' "
				"AND c.relkind = 'r');")
	rows = cur.fetchall()
	if rows[0][0] is False:
		cur.execute("CREATE TABLE iwkspc_folders(rowid SERIAL PRIMARY KEY, wid char(36) NOT NULL, "
					"enc_key VARCHAR(64) NOT NULL);")


	cur.execute("SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON "
				"n.oid = c.relnamespace WHERE n.nspname = 'public' AND c.relname = 'iwkspc_devices' "
				"AND c.relkind = 'r');")
	rows = cur.fetchall()
	if rows[0][0] is False:
		cur.execute("CREATE TABLE iwkspc_devices(rowid SERIAL PRIMARY KEY, wid CHAR(36) NOT NULL, "
					"devid CHAR(36) NOT NULL, devkey VARCHAR(1000) NOT NULL, "
					"lastlogin VARCHAR(32) NOT NULL, status VARCHAR(16) NOT NULL);")


	cur.execute("SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON "
				"n.oid = c.relnamespace WHERE n.nspname = 'public' AND c.relname = 'quotas' "
				"AND c.relkind = 'r');")
	rows = cur.fetchall()
	if rows[0][0] is False:
		cur.execute("CREATE TABLE quotas(rowid SERIAL PRIMARY KEY, wid CHAR(36) NOT NULL, "
				"usage BIGINT, quota BIGINT);")


	cur.execute("SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON "
				"n.oid = c.relnamespace WHERE n.nspname = 'public' AND c.relname = 'failure_log' "
				"AND c.relkind = 'r');")
	rows = cur.fetchall()
	if rows[0][0] is False:
		cur.execute("CREATE TABLE failure_log(rowid SERIAL PRIMARY KEY, type VARCHAR(16) NOT NULL, "
					"id VARCHAR(36), source VARCHAR(36) NOT NULL, count INTEGER, "
					"last_failure TIMESTAMP NOT NULL, lockout_until TIMESTAMP);")


	cur.execute("SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON "
				"n.oid = c.relnamespace WHERE n.nspname = 'public' AND c.relname = 'passcodes' "
				"AND c.relkind = 'r');")
	rows = cur.fetchall()
	if rows[0][0] is False:
		cur.execute("CREATE TABLE passcodes(rowid SERIAL PRIMARY KEY, wid VARCHAR(36) NOT NULL UNIQUE, "
					"passcode VARCHAR(128) NOT NULL, expires TIMESTAMP NOT NULL);")


	cur.execute("SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON "
				"n.oid = c.relnamespace WHERE n.nspname = 'public' AND c.relname = 'prereg' "
				"AND c.relkind = 'r');")
	rows = cur.fetchall()
	if rows[0][0] is False:
		cur.execute("CREATE TABLE prereg(rowid SERIAL PRIMARY KEY, wid VARCHAR(36) NOT NULL UNIQUE, "
					"uid VARCHAR(128) NOT NULL, domain VARCHAR(255) NOT NULL, regcode VARCHAR(128));")


	cur.execute("SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON "
				"n.oid = c.relnamespace WHERE n.nspname = 'public' AND c.relname = 'keycards' "
				"AND c.relkind = 'r');")
	rows = cur.fetchall()
	if rows[0][0] is False:
		cur.execute("CREATE TABLE keycards(rowid SERIAL PRIMARY KEY, owner VARCHAR(292) NOT NULL, "
					"creationtime TIMESTAMP NOT NULL, index INTEGER NOT NULL, "
					"entry VARCHAR(8192) NOT NULL, fingerprint VARCHAR(96) NOT NULL);")


	cur.execute("SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON "
				"n.oid = c.relnamespace WHERE n.nspname = 'public' AND c.relname = 'orgkeys' "
				"AND c.relkind = 'r');")
	rows = cur.fetchall()
	if rows[0][0] is False:
		cur.execute("CREATE TABLE orgkeys(rowid SERIAL PRIMARY KEY, creationtime TIMESTAMP NOT NULL, "
					"pubkey VARCHAR(7000), privkey VARCHAR(7000) NOT NULL, "
					"purpose VARCHAR(8) NOT NULL, fingerprint VARCHAR(96) NOT NULL);")


	cur.execute("SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON "
				"n.oid = c.relnamespace WHERE n.nspname = 'public' AND c.relname = 'updates' "
				"AND c.relkind = 'r');")
	rows = cur.fetchall()
	if rows[0][0] is False:
		cur.execute("CREATE TABLE updates(rowid SERIAL PRIMARY KEY, wid CHAR(36) NOT NULL, "
					"update_type INTEGER, update_data VARCHAR(2048), unixtime BIGINT);")

	conn.commit()


def populate_database(conn, config) -> dict:
	'''Adds basic data to the database as if setupconfig had been run. Returns data needed for 
	tests, such as the keys'''

	out = dict()

	# Start off by generating the org's root keycard entry and add to the database

	cur = conn.cursor()
	
	epair = EncryptionPair()
	pspair = SigningPair()

	timestamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
	
	cur.execute("INSERT INTO orgkeys(creationtime, pubkey, privkey, purpose, fingerprint) "
				"VALUES(%s,%s,%s,'encrypt',%s);",
				(timestamp, str(epair.public), str(epair.private), str(epair.pubhash)))

	cur.execute(f"INSERT INTO orgkeys(creationtime, pubkey, privkey, purpose, fingerprint) "
				"VALUES(%s,%s,%s,'sign',%s);",
				(timestamp, str(pspair.public), str(pspair.private), str(pspair.pubhash)))

	rootentry = keycard.OrgEntry()
	rootentry.set_fields({
		'Name' : 'Example, Inc.',
		'Primary-Verification-Key' : str(pspair.public),
		'Encryption-Key' : str(epair.public),
		'Language': 'en'
	})

	# preregister the admin account and put into the serverconfig

	admin_wid = str(uuid.uuid4())
	admin_address = '/'.join([admin_wid,config['global']['domain']])
	out['admin'] = admin_address

	regcode = make_diceware()
	cur.execute(f"INSERT INTO prereg(wid, uid, domain, regcode) VALUES(%s, 'admin', %s, %s);",
		(admin_wid, config['global']['domain'], regcode))

	out['admin_regcode'] = regcode
	rootentry.set_field('Contact-Admin', admin_address)

	# preregister the abuse account if not aliased and put into the serverconfig

	abuse_wid = str(uuid.uuid4())
	abuse_address = '/'.join([abuse_wid,config['global']['domain']])
	out['abuse'] = abuse_address
	rootentry.set_field('Contact-Abuse', abuse_address)

	cur.execute("INSERT INTO workspaces(wid, uid, domain, wtype, status) "
		"VALUES(%s, 'abuse', %s, 'alias', 'active');", (abuse_wid, config['global']['domain']))
	
	cur.execute("INSERT INTO aliases(wid, alias) VALUES(%s,%s);", (abuse_wid,
		'/'.join([admin_wid, config['global']['domain']])))


	# preregister the support account if not aliased and put into the serverconfig

	support_wid = str(uuid.uuid4())
	support_address = '/'.join([support_wid,config['global']['domain']])
	out['support'] = support_address
	rootentry.set_field('Contact-Support', support_address)

	cur.execute("INSERT INTO workspaces(wid, uid, domain, wtype, status) "
		"VALUES(%s, 'support', %s, 'alias', 'active');", (support_wid, config['global']['domain']))
	
	cur.execute("INSERT INTO aliases(wid, alias) VALUES(%s,%s);", (support_wid,
		'/'.join([admin_wid, config['global']['domain']])))

	status = rootentry.is_data_compliant()
	if status.error():
		print(f"There was a problem with the organization data: {status.info()}")
		sys.exit()

	status = rootentry.generate_hash('BLAKE2B-256')
	if status.error():
		print(f"Unable to generate the hash for the org keycard: {status.info()}")
		sys.exit()

	status = rootentry.sign(pspair.private, 'Organization')
	if status.error():
		print(f"Unable to sign the org keycard: {status.info()}")
		sys.exit()

	status = rootentry.generate_hash('BLAKE2B-256')
	if status.error():
		print(f"Unable to generate the hash for the org keycard: {status.info()}")
		sys.exit()

	status = rootentry.is_compliant()
	if status.error():
		print(f"There was a problem with the keycard's compliance: {status.info()}")
		sys.exit()

	cur.execute("INSERT INTO keycards(owner, creationtime, index, entry, fingerprint) "
				"VALUES(%s, %s, %s, %s, %s);",
				('organization', rootentry.fields['Timestamp'], 
				rootentry.fields['Index'], str(rootentry), rootentry.hash)
				)

	cur.close()
	conn.commit()

	return out


def reset_top_dir(config: dict):
	'''Resets the system workspace storage directory to an empty skeleton'''

	glob_list = glob(os.path.join(config['global']['top_dir'],'*'))
	for glob_item in glob_list:
		if os.path.isfile(glob_item):
			try:
				os.remove(glob_item)
			except:
				assert False, f"Unable to delete file {glob_item}"
		else:
			try:
				shutil.rmtree(glob_item)
			except:
				assert False, f"Unable to delete file {glob_item}"
	
	os.mkdir(os.path.join(config['global']['top_dir'],'out'), mode=0o770)
	os.mkdir(os.path.join(config['global']['top_dir'],'tmp'), mode=0o770)
	os.mkdir(os.path.join(config['global']['top_dir'],'wsp'), mode=0o770)


def make_diceware():
	'''Generates a diceware password'''
	options = argparse.Namespace()
	options.num = 5
	options.caps = True
	options.specials = 0
	options.delimiter = '-'
	options.randomsource = 'system'
	options.wordlist = 'en_eff'
	options.infile = None
	return diceware.get_passphrase(options)

import inspect
import os
import shutil
import time

from pymensago.userinfo import load_user_field
import pymensago.userprofile as userprofile
from pymensago.utils import MAddress
from retval import ErrNotFound

import iscmds
import server_reset
import shellbase
import shellcmds

def funcname() -> str: 
	frames = inspect.getouterframes(inspect.currentframe())
	return frames[1].function


def setup_test(name):
	'''Creates a test folder hierarchy'''
	test_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)),'testfiles')
	if not os.path.exists(test_folder):
		os.mkdir(test_folder)

	test_folder = os.path.join(test_folder, name)
	while os.path.exists(test_folder):
		try:
			shutil.rmtree(test_folder)
		except:
			print("Waiting a second for test folder to unlock")
			time.sleep(1.0)
	os.mkdir(test_folder)
	return test_folder


def test_myinfo():
	'''Tests the myinfo command'''
	test_folder = setup_test(funcname())
	shellstate = shellbase.ShellState(test_folder)
	profman = userprofile.profman
	data = server_reset.reset()
	status = shellstate.client.redeem_regcode(MAddress('admin/example.com'), data['admin_regcode'],
		'MyS3cretPassw*rd')
	assert not status.error(), f"{funcname()}: admin regcode failed: {status.error()}"
	
	cmd = iscmds.CommandMyInfo()
	cmdlist = [ 'myinfo set GivenName Corbin',
				'myinfo set FamilyName Simons',
				f"myinfo set Mensago.0.Workspace {data['admin']}",
				'myinfo set Mensago.0.Domain example.com',
				'myinfo set Mensago.0.UserID admin',
				f"myinfo set Mensago.1.Workspace {data['abuse']}",
				'myinfo set Mensago.1.Domain example.com',
				'myinfo set Mensago.1.UserID abuse',
				'myinfo set Annotations.Nicknames.0 Test1',
				'myinfo set Annotations.Nicknames.1 Test2',
				'myinfo set Annotations.Nicknames.2 Test3',
				]

	# Test setting + setup for other subtests
	for entry in cmdlist:
		status = cmd.set(entry)
		assert not status.error(), f"{funcname()}: command `{entry}` failed: {status.error()}"
		status = cmd.validate(shellstate)
		assert not status.error(), f"{funcname()}: validate('{entry}') failed: {status.error()}"
		status = cmd.execute(shellstate)
		assert not status.error(), f"{funcname()}: execute('{entry}') failed: {status.error()}"

	# Test getting
	status = cmd.set('myinfo get GivenName')
	assert not status.error(), f"{funcname()}: single get.set failed: {status.error()}"
	status = cmd.validate(shellstate)
	assert not status.error(), f"{funcname()}: single get.validate failed: {status.error()}"
	status = cmd.execute(shellstate)
	assert not status.error(), f"{funcname()}: single get.execute failed: {status.error()}"
	assert status['value'] == 'Corbin', f"{funcname()}: single get got wrong value {status['value']}"
	assert status['group'] == 'self', f"{funcname()}: single get got wrong group '{status['group']}'"

	status = cmd.set('myinfo get')
	assert not status.error(), f"{funcname()}: multiple get.set failed: {status.error()}"
	status = cmd.validate(shellstate)
	assert not status.error(), f"{funcname()}: multiple get.validate failed: {status.error()}"
	status = cmd.execute(shellstate)
	assert not status.error(), f"{funcname()}: multiple get.execute failed: {status.error()}"
	assert 'name' in status and len(status['name']) == len(cmdlist), \
		f"{funcname()}: multiple get got wrong number of names"
	assert 'value' in status and len(status['value']) == len(cmdlist), \
		f"{funcname()}: multiple get got wrong number of values"
	assert 'group' in status and len(status['group']) == len(cmdlist), \
		f"{funcname()}: multiple get got wrong number of groups"

	# Test deleting
	status = cmd.set('myinfo del Annotations.Nicknames.2')
	assert not status.error(), f"{funcname()}: del.set failed: {status.error()}"
	status = cmd.validate(shellstate)
	assert not status.error(), f"{funcname()}: del.validate failed: {status.error()}"
	status = cmd.execute(shellstate)
	assert not status.error(), f"{funcname()}: del.execute failed: {status.error()}"

	status = profman.get_active_profile()
	assert not status.error(), f"{funcname()}: failed to get active profile: {status.error()}"
	profile = status['profile']
	status = load_user_field(profile.db, 'Annotations.Nicknames.2')
	assert status.error() == ErrNotFound, \
		f"{funcname()}: del failed to delete value: {status.error()}"

	# repeating the del test -- deleting a nonexistent field should return no error
	status = cmd.set('myinfo del Annotations.Nicknames.2')
	assert not status.error(), f"{funcname()}: del.set failed: {status.error()}"
	status = cmd.validate(shellstate)
	assert not status.error(), f"{funcname()}: del.validate failed: {status.error()}"
	status = cmd.execute(shellstate)
	assert not status.error(), f"{funcname()}: del.execute failed: {status.error()}"

	# Erroneous set tests
	status = cmd.set('myinfo set Annotations.Nicknames.1 ""')
	assert not status.error(), f"{funcname()}: failed to set.set empty value: {status.error()}"
	status = cmd.validate(shellstate)
	assert status.error(), \
		f"{funcname()}: set.validate failed to catch empty value: {status.error()}"

	# Erroneous get tests
	status = cmd.set('myinfo get NonExistent')
	assert not status.error(), f"{funcname()}: get.set nonexistent failed: {status.error()}"
	status = cmd.validate(shellstate)
	assert not status.error(), f"{funcname()}: get.validate nonexistent failed: {status.error()}"
	status = cmd.execute(shellstate)
	assert status.error(), f"{funcname()}: get.execute failed to catch nonexistent field"


def test_myinfo_check():
	'''Tests the myinfo check subcommand'''
	test_folder = setup_test(funcname())
	shellstate = shellbase.ShellState(test_folder)
	_ = userprofile.profman
	data = server_reset.reset()
	status = shellstate.client.redeem_regcode(MAddress('admin/example.com'), data['admin_regcode'],
		'MyS3cretPassw*rd')
	assert not status.error(), f"{funcname()}: admin regcode failed: {status.error()}"
	
	cmd = iscmds.CommandMyInfo()
	cmdlist = [ 'myinfo set GivenName Corbin',
				'myinfo set FamilyName Simons',
				f"myinfo set Mensago.0.Workspace {data['admin']}",
				'myinfo set Mensago.0.Domain example.com',
				'myinfo set Mensago.0.UserID admin',
				f"myinfo set Mensago.1.Workspace {data['abuse']}",
				'myinfo set Mensago.1.Domain example.com',
				'myinfo set Mensago.1.UserID abuse',
				]

	# Test setup
	for entry in cmdlist:
		status = cmd.set(entry)
		assert not status.error(), f"{funcname()}: command `{entry}` failed: {status.error()}"
		status = cmd.validate(shellstate)
		assert not status.error(), f"{funcname()}: validate('{entry}') failed: {status.error()}"
		status = cmd.execute(shellstate)
		assert not status.error(), f"{funcname()}: execute('{entry}') failed: {status.error()}"

	# Contact info is so far not compliant
	status = cmd.set('myinfo check')
	assert not status.error(), f"{funcname()}: check failed: {status.error()}"
	status = cmd.validate(shellstate)
	assert not status.error(), f"{funcname()}: check failed: {status.error()}"
	status = cmd.execute(shellstate)
	assert status.error(), f"{funcname()}: check failed to catch noncompliance: {status.error()}"
	assert 'missing' in status and len(status['missing']) == 2, \
		f"{funcname()}: check returned wrong missing fields"

	# Set two fields and it will be
	cmdlist = [ f"myinfo set Mensago.0.Label Admin",
				f"myinfo set Mensago.1.Label Abuse",
			]

	for entry in cmdlist:
		status = cmd.set(entry)
		assert not status.error(), f"{funcname()}: command `{entry}` failed: {status.error()}"
		status = cmd.validate(shellstate)
		assert not status.error(), f"{funcname()}: validate('{entry}') failed: {status.error()}"
		status = cmd.execute(shellstate)
		assert not status.error(), f"{funcname()}: execute('{entry}') failed: {status.error()}"
	
	status = cmd.set('myinfo check')
	assert not status.error(), f"{funcname()}: check failed: {status.error()}"
	status = cmd.validate(shellstate)
	assert not status.error(), f"{funcname()}: check failed: {status.error()}"
	status = cmd.execute(shellstate)
	assert not status.error(), f"{funcname()}: check: {status.error()}"


def test_regcode():
	'''Tests the regcode command'''
	test_folder = setup_test(funcname())
	shellstate = shellbase.ShellState(test_folder)
	profman = userprofile.profman

	cmd = iscmds.CommandRegCode()
	cmdlist = [ 'regcode <ADMINWID> <REGCODE> MyS3cretPassw*rd',
				'regcode admin/example.com <REGCODE> MyS3cretPassw*rd' ]

	for entry in cmdlist:
		pnames = [p.name for p in profman.get_profiles()]
		if funcname() in pnames:
			profman.activate_profile('primary')
			profman.delete_profile(funcname())
		
		profman.create_profile(funcname())
		profman.activate_profile(funcname())

		data = server_reset.reset()
		
		entry = entry.replace('<ADMINWID>', data['admin'])
		entry = entry.replace('<REGCODE>', data['admin_regcode'])

		status = cmd.set(entry)
		assert not status.error(), f"{funcname()}: set('{entry}') failed: {status.error()}"
		status = cmd.validate(shellstate)
		assert not status.error(), f"{funcname()}: validate('{entry}') failed: {status.error()}"
		status = cmd.execute(shellstate)
		assert not status.error(), f"{funcname()}: execute('{entry}') failed: {status.error()}"
	
	status = cmd.set('regcode admin/example.com Shouldnt-Matter ThisShouldFail')
	assert not status.error(), f"{funcname()}: final set failed"
	status = cmd.validate(shellstate)
	assert status.error(), f"{funcname()}: validate passed registering while an identity exists"


def test_preregister_plus():
	'''Tests the complete preregistration process each of the several ways'''
	test_folder = setup_test(funcname())
	shellstate = shellbase.ShellState(test_folder)
	profman = userprofile.profman

	data = server_reset.reset()
	status = shellstate.client.redeem_regcode(MAddress('admin/example.com'), data['admin_regcode'],
		'MyS3cretPassw*rd')
	assert not status.error(), f"{funcname()}: admin regcode failed: {status.error()}"

	cmd = iscmds.CommandPreregister()
	cmdlist = [ 'preregister csimons', 'preregister csimons2 example.com' ]

	for entry in cmdlist:
		pnames = [p.name for p in profman.get_profiles()]
		if funcname() in pnames:
			profman.activate_profile('primary')
			profman.delete_profile(funcname())
		
		status = shellstate.client.login(MAddress('admin/example.com'))
		assert not status.error(), f"{funcname()}: Failed to log in as admin: " \
			f"{status.error()} / {status.info()}"
		
		# Preregistration
		status = cmd.set(entry)
		assert not status.error(), f"{funcname()}: set('{entry}') failed: {status.error()}"
		status = cmd.validate(shellstate)
		assert not status.error(), f"{funcname()}: validate('{entry}') failed: {status.error()}"
		status = cmd.execute(shellstate)
		assert not status.error(), f"{funcname()}: execute('{entry}') failed: {status.error()}"
		regdata = status

		status = shellstate.client.logout()
		assert not status.error(), f"{funcname()}: Failed to log out of admin account: " \
			f"{status.error()} / {status.info()}"

		# Load up a throwaway profile for the newly-preregistered account, activate it, apply the
		# registration code, and log in as the user
		profman.create_profile(funcname())
		profman.activate_profile(funcname())

		addr = MAddress()
		if regdata.has_value('uid'):
			addr.set_from_userid(regdata['uid'], regdata['domain'])
		else:
			addr.set_from_wid(regdata['wid'], regdata['domain'])
		status = shellstate.client.redeem_regcode(addr, regdata['regcode'], 'MyS3cretPassw*rd')
		assert not status.error(), f"{funcname()}: Failed to redeem user regcode"

		status = shellstate.client.login(addr)
		assert not status.error(), f"{funcname()}: Failed to log in as user {addr.as_string()}"
		status = shellstate.client.logout()
		assert not status.error(), f"{funcname()}: Failed to log out from user {addr.as_string()}"
	
	shellstate.client.disconnect()


def test_profile():
	'''Tests the different profile command modes'''
	test_folder = setup_test(funcname())
	shellstate = shellbase.ShellState(test_folder)
	profman = userprofile.profman

	data = server_reset.reset()
	status = shellstate.client.redeem_regcode(MAddress('admin/example.com'), data['admin_regcode'],
		'MyS3cretPassw*rd')
	assert not status.error(), f"{funcname()}: admin regcode failed: {status.error()}"

	cmd = shellcmds.CommandProfile()
	status = cmd.set('profile')
	assert not status.error(), f"{funcname()}: set('profile') failed: {status.error()}"
	status = cmd.validate(shellstate)
	assert not status.error(), f"{funcname()}: validate('profile') failed: {status.error()}"
	status = cmd.execute(shellstate)
	assert not status.error(), f"{funcname()}: execute('profile') failed: {status.error()}"
	assert status.info() == 'Active profile: primary, admin/example.com', \
		f"{funcname()}: execute('profile') failed: output did not match expected: '{status.info()}'"

	teststr = f"profile create {funcname()}"
	status = cmd.set(teststr)
	assert not status.error(), f"{funcname()}: set('{teststr}') failed: {status.error()}"
	status = cmd.validate(shellstate)
	assert not status.error(), f"{funcname()}: validate('{teststr}') failed: {status.error()}"
	status = cmd.execute(shellstate)
	assert not status.error(), f"{funcname()}: execute('{teststr}') failed: {status.error()}"

	teststr = f"profile create Fancy*Profile@Name"
	status = cmd.set(teststr)
	assert not status.error(), f"{funcname()}: set('{teststr}') failed: {status.error()}"
	status = cmd.validate(shellstate)
	assert status.error(), f"{funcname()}: validate('{teststr}') passed a bad profile name"

	teststr = "profile list"
	status = cmd.set(teststr)
	assert not status.error(), f"{funcname()}: set('{teststr}') failed: {status.error()}"
	status = cmd.validate(shellstate)
	assert not status.error(), f"{funcname()}: validate('{teststr}') failed: {status.error()}"
	status = cmd.execute(shellstate)
	assert not status.error(), f"{funcname()}: execute('{teststr}') failed: {status.error()}"
	assert status.info() == f"Profiles:\nprimary\n{funcname()}"

	teststr = f"profile set {funcname()}"
	status = cmd.set(teststr)
	assert not status.error(), f"{funcname()}: set('{teststr}') failed: {status.error()}"
	status = cmd.validate(shellstate)
	assert not status.error(), f"{funcname()}: validate('{teststr}') failed: {status.error()}"
	status = cmd.execute(shellstate)
	assert not status.error(), f"{funcname()}: execute('{teststr}') failed: {status.error()}"

	teststr = f"profile set nonexistent-profile"
	status = cmd.set(teststr)
	assert not status.error(), f"{funcname()}: set('{teststr}') failed: {status.error()}"
	status = cmd.validate(shellstate)
	assert not status.error(), f"{funcname()}: validate('{teststr}') failed: {status.error()}"
	status = cmd.execute(shellstate)
	assert status.error(), f"{funcname()}: execute('{teststr}') passed a nonexistent profile"

	# TODO: Finish writing profile command tests


def test_register():
	'''Tests the register command'''
	test_folder = setup_test(funcname())
	shellstate = shellbase.ShellState(test_folder)
	profman = userprofile.profman
	
	data = server_reset.reset()
	status = shellstate.client.redeem_regcode(MAddress('admin/example.com'), data['admin_regcode'],
		'MyS3cretPassw*rd')
	assert not status.error(), f"{funcname()}: admin regcode failed: {status.error()}"

	status = profman.create_profile('testuser')
	assert not status.error(), f"{funcname()}: failed to create test user profile: {status.error()}"
	status = profman.activate_profile('testuser')
	assert not status.error(), f"{funcname()}: failed to activate test user profile: {status.error()}"

	cmd = iscmds.CommandRegister()
	cmdlist = [ 'register example.com "Corbin Simons" userid=csimons password=MyS3cretPassw*rd' ]
	# TODO: Add other registration test cases

	for entry in cmdlist:
		pnames = [p.name for p in profman.get_profiles()]
		if funcname() in pnames:
			profman.activate_profile('primary')
			profman.delete_profile(funcname())
		
		profman.create_profile(funcname())
		profman.activate_profile(funcname())

		server_reset.reset()

		status = cmd.set(entry)
		assert not status.error(), f"{funcname()}: set('{entry}') failed: {status.error()}"
		status = cmd.validate(shellstate)
		assert not status.error(), f"{funcname()}: validate('{entry}') failed: {status.error()}"
		status = cmd.execute(shellstate)
		assert not status.error(), f"{funcname()}: execute('{entry}') failed: {status.error()}"
	

if __name__ == '__main__':
	# test_login_logout()
	# test_myinfo()
	# test_myinfo_check()
	# test_preregister_plus()
	# test_profile()
	# test_regcode()
	test_register()

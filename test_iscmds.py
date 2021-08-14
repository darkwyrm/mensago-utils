import inspect
import os
import shutil
import time

import pymensago.userprofile as userprofile
from pymensago.utils import MAddress

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
	
	cmd = iscmds.CommandMyInfo()
	cmdlist = [ 'myinfo set GivenName Corbin',
				'myinfo set FamilyName Simons',
				f"myinfo set Mensago.0.Workspace {data['admin']}",
				'myinfo set Mensago.0.Domain example.com',
				'myinfo set Mensago.0.UserID admin',
				f"myinfo set Mensago.1.Workspace {data['abuse']}",
				'myinfo set Mensago.1.Domain example.com',
				'myinfo set Mensago.1.UserID abuse' ]

	for entry in cmdlist:
		status = cmd.set(entry)
		assert not status.error(), f"{funcname()}: command `{entry}` failed: {status.error()}"
		status = cmd.validate(shellstate)
		assert not status.error(), f"{funcname()}: validate('{entry}') failed: {status.error()}"
		status = cmd.execute(shellstate)
		assert not status.error(), f"{funcname()}: execute('{entry}') failed: {status.error()}"


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
	test_myinfo()
	# test_preregister_plus()
	# test_profile()
	# test_regcode()
	# test_register()

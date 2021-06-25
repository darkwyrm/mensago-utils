import inspect
import os
import platform
import shutil
import time

import pymensago.userprofile as userprofile
from retval import RetVal

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


def test_parsing():
	'''Tests the baseline command parsing in BaseCommand'''
	
	cmd = shellbase.BaseCommand()

	# Subtest #1: Basic arguments
	status = cmd.set('cmd foo bar baz')
	assert not status.error(), f"{funcname()}: #1 failed to tokenize basic arguments"
	assert len(cmd.tokens) == 3, f"{funcname()}: #1 had wrong token count"

	# Subtest #2: Quote handling
	status = cmd.set('cmd foo "bar baz"')
	assert not status.error(), f"{funcname()}: #2 failed to tokenize quoted arguments"
	assert len(cmd.tokens) == 2, f"{funcname()}: #2 had wrong token count"

	# Subtest #3: Escape handling
	status = cmd.set('cmd foo "bar %"baz%" "')
	assert not status.error(), f"{funcname()}: #3 failed to tokenize quoted arguments"
	assert len(cmd.tokens) == 2, f"{funcname()}: #3 had wrong token count"
	assert cmd.tokens[1] == 'bar "baz" ', f"{funcname()}: #3 failed to handle quote escaping"

	# Subtest #4: Named arguments
	status = cmd.set('cmd foo bar=baz')
	assert not status.error(), f"{funcname()}: #4 failed to parse tokenize arguments"
	assert len(cmd.tokens) == 1, f"{funcname()}: #4 had wrong token count"
	assert 'bar' in cmd.args and cmd.args['bar'] == 'baz', \
		f"{funcname()}: #4 failed to parse named arguments"

	# Subtest #5: Quoted named arguments
	status = cmd.set('cmd foo "bar=spam eggs"')
	assert not status.error(), f"{funcname()}: #5 failed to parse tokenize arguments"
	assert len(cmd.tokens) == 1, f"{funcname()}: #5 had wrong token count"
	assert 'bar' in cmd.args and cmd.args['bar'] == 'spam eggs', \
		f"{funcname()}: #5 failed to parse named arguments"


def test_chdir():
	'''Basic tests for chdir'''
	status = RetVal()
	shellstate = shellbase.ShellState()

	cmd = shellcmds.CommandChDir()
	cwd = os.getcwd()

	if platform.system().casefold() == 'windows':
		status = cmd.set(r'chdir C:\\')
	else:
		status = cmd.set(r'chdir /')
	assert not status.error(), f"{funcname()}: set('/') failed: {status.error()}"
	status = cmd.validate(shellstate)
	assert not status.error(), f"{funcname()}: validate('/') failed: {status.error()}"
	status = cmd.execute(shellstate)
	assert not status.error(), f"{funcname()}: execute('/') failed: {status.error()}"

	status = cmd.set(r'chdir ~')
	assert not status.error(), f"{funcname()}: set('~') failed: {status.error()}"
	status = cmd.validate(shellstate)
	assert not status.error(), f"{funcname()}: validate('~') failed: {status.error()}"
	status = cmd.execute(shellstate)
	assert not status.error(), f"{funcname()}: execute('~') failed: {status.error()}"


def test_listdir():
	'''Basic tests for listdir'''
	status = RetVal()
	shellstate = shellbase.ShellState()

	cmd = shellcmds.CommandListDir()
	dirlist = ['~']
	if platform.system().casefold() == 'windows':
		dirlist.append(r'ls C:\\')
	else:
		dirlist.append(r'ls /')
	
	for dir in dirlist:
		status = cmd.set(dir)
		assert not status.error(), f"{funcname()}: set('{dir}') failed: {status.error()}"
		status = cmd.validate(shellstate)
		assert not status.error(), f"{funcname()}: validate('{dir}') failed: {status.error()}"
		status = cmd.execute(shellstate)
		assert not status.error(), f"{funcname()}: execute('{dir}') failed: {status.error()}"


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
	test_parsing()
	test_chdir()
	test_listdir()
	test_regcode()
	test_register()

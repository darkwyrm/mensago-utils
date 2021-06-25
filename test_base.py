import inspect
import os
import platform

from retval import RetVal

import shellbase
import shellcmds

def funcname() -> str: 
	frame = inspect.currentframe()
	return inspect.getframeinfo(frame).function

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
	assert not status.error(), f"{funcname()}: set('/') failed"
	status = cmd.validate(shellstate)
	assert not status.error(), f"{funcname()}: validate('/') failed"
	status = cmd.execute(shellstate)
	assert not status.error(), f"{funcname()}: execute('/') failed"

	status = cmd.set(r'chdir ~')
	assert not status.error(), f"{funcname()}: set('~') failed"
	status = cmd.validate(shellstate)
	assert not status.error(), f"{funcname()}: validate('~') failed"
	status = cmd.execute(shellstate)
	assert not status.error(), f"{funcname()}: execute('~') failed"
	os.chdir(cwd)


def test_listdir():
	'''Basic tests for listdir'''
	status = RetVal()
	shellstate = shellbase.ShellState()

	testcmd = 'chdir'
	testcmd = 'ls'
	cmd = shellcmds.CommandListDir()
	status = cmd.set(r'ls ~')
	assert not status.error(), f"{funcname()}: set('~') failed"
	status = cmd.validate(shellstate)
	assert not status.error(), f"{funcname()}: validate('~') failed"
	status = cmd.execute(shellstate)
	assert not status.error(), f"{funcname()}: execute('~') failed"


if __name__ == '__main__':
	test_parsing()
	test_chdir()
	test_listdir()


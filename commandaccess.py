import collections
from shellbase import BaseCommand, gShellCommands
import string
import sys

from prompt_toolkit import HTML

import shellhelp
import iscmds
import shellcmds 

__aliases = dict()
__all_names = list()

def init_commands():
	add_command(shellcmds.CommandChDir())
	add_command(shellcmds.CommandListDir())
	add_command(shellcmds.CommandExit())
	add_command(shellcmds.CommandHelp())
	add_command(shellcmds.CommandShell())
	add_command(shellcmds.CommandProfile())
	add_command(shellcmds.CommandResetDB())

	add_command(iscmds.CommandLogin())
	add_command(iscmds.CommandLogout())
	add_command(iscmds.CommandPreregister())
	add_command(iscmds.CommandRegCode())
	add_command(iscmds.CommandRegister())

	global __all_names
	__all_names.sort()

	# Create the help topic for the command list
	ordered = collections.OrderedDict(sorted(gShellCommands.items()))
	parts = list()

	maxlength = 0
	for name,_ in ordered.items():
		if len(name) > maxlength:
			maxlength = len(name)
	
	for name,item in ordered.items():
		parts.append(f"<gray><b>{name.rjust(maxlength)}</b>  {item.description}</gray>")
	shellhelp.addtopic('commands', '\n'.join(parts), None)


def add_command(cmd: BaseCommand):
	'''Add a Command instance to the list'''

	global __all_names, __aliases

	shellcmds.gShellCommands[cmd.name] = cmd
	__all_names.append(cmd.name)
	
	for k,v in cmd.get_aliases().items():
		if k in __aliases:
			print(f"Error duplicate alias {k}. Already exists for {__aliases[k]}")
			sys.exit(0)
		__aliases[k] = v
		__all_names.append(k)


def get_command(name: str):
	'''Retrives a Command instance for the specified name, including alias resolution.'''

	global __aliases

	if len(name) < 1:
		return shellcmds.CommandEmpty()

	if name in __aliases:
		name = __aliases[name]

	if name in shellcmds.gShellCommands:
		return shellcmds.gShellCommands[name]

	return shellcmds.CommandUnrecognized()


def get_command_names():
	'''Get the names of all available commands'''
	
	global __all_names
	return __all_names

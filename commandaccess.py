from shellbase import BaseCommand
import sys

import shellcommands 

__aliases = dict()
__all_names = list()

def init_commands():
	add_command(shellcommands.CommandChDir())
	add_command(shellcommands.CommandListDir())
	add_command(shellcommands.CommandExit())
	add_command(shellcommands.CommandHelp())
	add_command(shellcommands.CommandShell())

	add_command(shellcommands.CommandPreregister())
	add_command(shellcommands.CommandProfile())
	add_command(shellcommands.CommandRegister())

	global __all_names
	__all_names.sort()


def add_command(cmd: BaseCommand):
	'''Add a Command instance to the list'''

	global __all_names, __aliases

	shellcommands.gShellCommands[cmd.name] = cmd
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
		return shellcommands.CommandEmpty()

	if name in __aliases:
		name = __aliases[name]

	if name in shellcommands.gShellCommands:
		return shellcommands.gShellCommands[name]

	return shellcommands.CommandUnrecognized()


def get_command_names():
	'''Get the names of all available commands'''
	
	global __all_names
	return __all_names

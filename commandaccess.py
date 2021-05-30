import sys

import shellcommands 

__aliases = dict()
__all_names = list()

def init_commands():
	add_command(shellcommands.CommandListDir())
	add_command(shellcommands.CommandExit())
	add_command(shellcommands.CommandHelp())
	add_command(shellcommands.CommandShell())

	add_command(shellcommands.CommandPreregister())
	add_command(shellcommands.CommandProfile())
	add_command(shellcommands.CommandRegister())
	add_command(shellcommands.CommandSetUserID())

	global __all_names
	__all_names.sort()


def add_command(pCommand):
	'''Add a Command instance to the list'''

	global __all_names, __aliases

	shellcommands.gShellCommands[pCommand.name] = pCommand
	__all_names.append(pCommand.name)
	for k,v in pCommand.get_aliases().items():
		if k in __aliases:
			print(f"Error duplicate alias {k}. Already exists for {__aliases[k]}")
			sys.exit(0)
		__aliases[k] = v
		__all_names.append(k)


def get_command(pName):
	'''Retrives a Command instance for the specified name, including alias resolution.'''

	global __aliases

	if len(pName) < 1:
		return shellcommands.CommandEmpty()

	if pName in __aliases:
		pName = __aliases[pName]

	if pName in shellcommands.gShellCommands:
		return shellcommands.gShellCommands[pName]

	return shellcommands.CommandUnrecognized()


def get_command_names():
	'''Get the names of all available commands'''
	
	global __all_names
	return __all_names

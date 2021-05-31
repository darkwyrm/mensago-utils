'''Contains the implementations for shell commands'''
# pylint: disable=unused-argument,too-many-branches
import collections
from getpass import getpass
from glob import glob
import os
import platform
import subprocess
import sys

from prompt_toolkit import print_formatted_text, HTML
from retval import ErrBadData, ErrBadValue, ErrEmptyData, ErrNotFound, ErrOK, ErrServerError, ErrUnimplemented, RetVal

from pymensago.encryption import check_password_complexity
import pymensago.errorcodes as errorcodes
from pymensago.utils import validate_userid

import helptext
from shellbase import BaseCommand, gShellCommands, ShellState

class CommandEmpty(BaseCommand):
	'''Special command just to handle blanks'''

	def __init__(self):
		super().__init__()
		self.name = ''


class CommandUnrecognized(BaseCommand):
	'''Special class for handling anything the shell doesn't support'''

	def __init__(self):
		super().__init__()
		self.name = 'unrecognized'

	def execute(self, shellstate: ShellState) -> RetVal:
		return RetVal(ErrNotFound, 'Unknown command')


class CommandChDir(BaseCommand):
	'''Change directories'''
	def __init__(self):
		super().__init__()
		self.name = 'chdir'
		self.help = 'Usage: cd <location>\nChanges to the specified directory\n\n' + \
						'Aliases: cd'
		self.description = 'change directory/location'

	def get_aliases(self) -> dict:
		return { 'cd': 'chdir' }

	def execute(self, shellstate: ShellState) -> RetVal:
		if self.tokens:
			new_dir = ''
			if '~' in self.tokens[0]:
				if platform.system().casefold() == 'windows':
					new_dir = self.tokens[0].replace('~', os.getenv('USERPROFILE'))
				else:
					new_dir = self.tokens[0].replace('~', os.getenv('HOME'))
			else:
				new_dir = self.tokens[0]
			try:
				os.chdir(new_dir)
			except Exception as e:
				return RetVal().wrap_exception(e)

		shellstate.oldpwd = shellstate.pwd
		shellstate.pwd = os.getcwd()

		return RetVal()

	def autocomplete(self, tokens: list, shellstate: ShellState):
		if len(tokens) == 1:
			out_data = list()
			
			quote_mode = bool(tokens[0][0] == '"')
			if quote_mode:
				items = glob(tokens[0][1:] + '*')
			else:
				items = glob(tokens[0] + '*')
			
			for item in items:
				if not os.path.isdir(item):
					continue

				display = item
				if quote_mode or ' ' in item:
					data = '"' + item + '"'
				else:
					data = item
				out_data.append([data,display])
					
			return out_data
		return list()


class CommandExit(BaseCommand):
	'''Exit the program'''
	def __init__(self):
		super().__init__()
		self.name = 'exit'
		self.help = 'Usage: exit\nCloses the connection and exits the shell.'
		self.description = 'Exits the shell'

	def get_aliases(self) -> dict:
		return { "x":"exit", "q":"exit" }

	def execute(self, shellstate: ShellState) -> RetVal:
		sys.exit(0)


class CommandHelp(BaseCommand):
	'''Implements the help system'''
	def __init__(self):
		super().__init__()
		self.name = 'help'
		self.help = 'Usage: help <command>\nProvides information on a command.\n\n' + \
						'Aliases: ?'
		self.description = 'Show help on a command'

	def get_aliases(self) -> dict:
		return { "?":"help" }

	def execute(self, shellstate: ShellState) -> RetVal:
		out = ''
		if self.tokens:
			# help <keyword>
			if self.tokens[0] in gShellCommands:
				out = gShellCommands[self.tokens[0]].help
			else:
				out = HTML(f"No help on <gray><b>{self.tokens[0]}</b></gray>\n")
			return RetVal(ErrOK, out)	
		
		# Bare help command: print available commands
		ordered = collections.OrderedDict(sorted(gShellCommands.items()))
		for name,item in ordered.items():
			print_formatted_text(HTML(f"<gray><b>{name}</b>\t{item.description}</gray>"))
		
		return RetVal()


class CommandListDir(BaseCommand):
	'''Performs a directory listing by calling the shell'''
	def __init__(self):
		super().__init__()
		self.name = 'ls'
		self.help = 'Usage: as per bash ls command or Windows dir command'
		self.description = 'list directory contents'

	def get_aliases(self) -> dict:
		return { "dir":"ls" }

	def execute(self, shellstate: ShellState) -> RetVal:
		if sys.platform == 'win32':
			tokens = ['dir','/w']
			tokens.extend(self.tokens)
			subprocess.call(tokens, shell=True)
		else:
			tokens = ['ls','--color=auto']
			tokens.extend(self.tokens)
			subprocess.call(tokens)
		
		return RetVal()

	def autocomplete(self, tokens: list, shellstate: ShellState):
		if len(tokens) == 1:
			out_data = list()
			
			if tokens[0][0] == '"':
				quote_mode = True
			else:
				quote_mode = False
			
			if quote_mode:
				items = glob(tokens[0][1:] + '*')
			else:
				items = glob(tokens[0] + '*')
			
			for item in items:
				if not os.path.isdir(item):
					continue

				display = item
				if quote_mode or ' ' in item:
					data = '"' + item + '"'
				else:
					data = item
				out_data.append([data,display])
					
			return out_data
		return list()


class CommandProfile(BaseCommand):
	'''User profile management command'''
	def __init__(self):
		super().__init__()
		self.name = 'profile'
		self.help = helptext.profile_cmd
		self.description = 'Manage profiles.'
	
	def execute(self, shellstate: ShellState) -> RetVal:
		if not self.tokens:
			status = shellstate.client.get_active_profile()
			if status.error():
				status.set_info('No active profile')
			else:
				status.set_info(f"Active profile: {status['profile'].name}")
			return status

		verb = self.tokens[0].casefold()
		if len(self.tokens) == 1:
			if verb == 'list':
				print("Profiles:")
				profiles = shellstate.client.get_profiles()
				for profile in profiles:
					print(profile.name)
			else:
				print(self.help)
			return ''

		if verb == 'create':
			status = shellstate.client.create_profile(self.tokens[1])
			if status.error():
				status.set_info(f"Couldn't create profile: {status.info()}")
			return status
		
		if verb == 'delete':
			print("This will delete the profile and all of its files. It can't be undone.")
			choice = input(f"Really delete profile '{self.tokens[1]}'? [y/N] ").casefold()
			status = RetVal()
			if choice in [ 'y', 'yes' ]:
				status = shellstate.client.delete_profile(self.tokens[1])
				if status.error():
					status.set_info(f"Couldn't delete profile: {status.info()}")
				else:
					status.set_info(f"Profile 'self.tokens[1]' has been deleted")
			return status
		
		if verb == 'set':
			status = shellstate.client.activate_profile(self.tokens[1])
			if status.error():
				status.set_info(f"Couldn't activate profile: {status.info()}")
			return status
		
		if verb == 'setdefault':
			status = shellstate.client.set_default_profile(self.tokens[1])
			if status.error():
				status.set_info(f"Couldn't set profile as default: {status.info()}")
			return status
		
		if verb == 'rename':
			if len(self.tokens) != 3:
				return RetVal(ErrEmptyData, self.help)
			status = shellstate.client.rename_profile(self.tokens[1], self.tokens[2])
			if status.error():
				status.set_info(f"Couldn't rename profile: {status.info()}")
			return status
		
		return RetVal(ErrOK, self.help)

	def autocomplete(self, tokens: list, shellstate: ShellState):
		if len(tokens) < 1:
			return list()

		verbs = [ 'create', 'delete', 'list', 'rename' ]
		if len(tokens) == 1 and tokens[0] not in verbs:
			out_data = [i for i in verbs if i.startswith(tokens[0])]
			return out_data
		
		groups = shellstate.client.get_profiles()
		if len(tokens) == 2 and tokens[1] not in groups:
			out_data = [i for i in groups if i.startswith(tokens[1])]
			return out_data

		return list()


class CommandSetInfo(BaseCommand):
	'''Set workspace information'''
	def __init__(self):
		super().__init__()
		self.name = 'setinfo'
		self.help = helptext.setinfo_cmd
		self.description = 'Set workspace information'

	def execute(self, shellstate: ShellState) -> RetVal:
		# TODO: Implement SETINFO
		return RetVal(ErrUnimplemented, 'Not implemented yet. Sorry!')


class CommandShell(BaseCommand):
	'''Perform shell commands'''
	def __init__(self):
		super().__init__()
		self.name = 'shell'
		self.help = helptext.shell_cmd
		self.description = 'Run a shell command'

	def get_aliases(self) -> dict:
		'''Return aliases for the command'''
		return { "sh":"shell", "`":"shell" }

	def execute(self, shellstate: ShellState) -> RetVal:
		status = RetVal()
		try:
			os.system(' '.join(self.tokens))
		except Exception as e:
			status.set_info(f"Error running command: {str(e)}")
		
		return status

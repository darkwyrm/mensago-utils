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
from retval import RetVal, ErrBadData, ErrEmptyData, ErrFilesystemError, ErrNotFound, ErrOK, \
	ErrUnimplemented

import pymensago.errorcodes as errorcodes

import helptext
import server_reset
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
		returncode = 0

		if len(self.tokens) > 0 and self.tokens[0].startswith('~'):
			if platform.system().casefold() == 'windows':
				self.tokens[0] = self.tokens[0].replace('~', os.getenv('USERPROFILE'))
			else:
				self.tokens[0] = self.tokens[0].replace('~', os.getenv('HOME'))
		
		if sys.platform == 'win32':
			tokens = ['dir','/w']
			tokens.extend(self.tokens)
			returncode = subprocess.call(tokens, shell=True)
		else:
			tokens = ['ls','--color=auto']
			tokens.extend(self.tokens)
			returncode = subprocess.call(tokens)

		if returncode == 0:		
			return RetVal()
		
		return RetVal(ErrFilesystemError, '')

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
	
	def validate(self, shellstate: ShellState) -> RetVal:
		if not len(self.tokens):
			self.args['verb'] = 'get'
			return RetVal()
		
		verb = self.tokens[0].casefold()
		self.args['verb'] = verb
		
		if verb in ['list', 'get']:
			return RetVal()
		
		if verb not in ['create', 'delete', 'rename', 'setdefault', 'set']:
			return RetVal(ErrBadData, self.help)
		
		if verb == 'rename':
			if len(self.tokens) != 3:
				return RetVal(ErrBadData, self.help)
			
			oldname = self.tokens[1].casefold()
			newname = self.tokens[2].casefold()
			if oldname == 'default' or newname == 'default':
				return RetVal(ErrBadData, "'default' is reserved and may not be used.")
			
			self.args['oldname'] = oldname
			self.args['newname'] = newname

			return RetVal()

		if len(self.tokens) != 2:
			return RetVal(ErrBadData, self.help)
		
		name = self.tokens[1].casefold()
		if name == 'default':
			return RetVal(ErrBadData, "'default' is reserved and may not be used.")
		
		self.args['name'] = name
		
		return RetVal()
		
	def execute(self, shellstate: ShellState) -> RetVal:
		verb = self.args['verb']
		
		if verb == 'get':
			status = shellstate.client.pman.get_active_profile()
			if status.error():
				status.set_info('No active profile')
			else:
				profile = status['profile']
				out = f"Active profile: {profile.name}, {profile.get_identity().as_string()}"
				status.set_info(out)
			return status

		if verb == 'list':
			print("Profiles:")
			profiles = shellstate.client.pman.get_profiles()
			for profile in profiles:
				print(profile.name)
			return RetVal()
			
		if verb == 'create':
			status = shellstate.client.pman.create_profile(self.args['name'])
			if status.error():
				status.set_info(f"Couldn't create profile: {status.error()} / {status.info()}")
			return status
		
		if verb == 'delete':
			print("This will delete the profile and all of its files. It can't be undone.")
			choice = input(f"Really delete profile '{self.args['name']}'? [y/N] ").casefold()
			status = RetVal()
			if choice in [ 'y', 'yes' ]:
				status = shellstate.client.pman.delete_profile(self.args['name'])
				if status.error():
					status.set_info(f"Couldn't delete profile: {status.error()} / {status.info()}")
				else:
					status.set_info(f"Profile '{self.args['name']}' has been deleted")
			return status
		
		if verb == 'set':
			status = shellstate.client.activate_profile(self.args['name'])
			if status.error():
				status.set_info(f"Couldn't activate profile: {status.error()} / {status.info()}")
			return status
		
		if verb == 'setdefault':
			status = shellstate.client.pman.set_default_profile(self.args['name'])
			if status.error():
				status.set_info(f"Couldn't set profile as default: "
					f"{status.error()} / {status.info()}")
			return status
		
		if verb == 'rename':
			if len(self.tokens) != 3:
				return RetVal(ErrEmptyData, self.help)
			status = shellstate.client.pman.rename_profile(self.args['oldname'],
				self.args['newname'])
			if status.error():
				status.set_info(f"Couldn't rename profile: {status.error()} / {status.info()}")
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


class CommandResetDB(BaseCommand):
	'''Dev command to reset the server database'''
	def __init__(self):
		super().__init__()
		self.name = 'resetdb'
		self.help = helptext.resetdb_cmd
		self.description = 'DEVELOPER: Completely resets the local Mensago database'
	
	def execute(self, shellstate: ShellState) -> RetVal:
		choice = input("This will delete ALL DATA in the local database.\n"
						"Are you sure? [y/N] ").casefold()
		
		if choice not in ['y', 'Y']:
			return RetVal()

		data = server_reset.reset()

		return RetVal(ErrOK, f"Administrator workspace: {data['admin']}\n"
							f"Administrator registration code: {data['admin_regcode']}\n"
							f"Abuse workspace (forwarded): {data['abuse']}\n"
							f"Support workspace (forwarded): {data['support']}\n")

'''Contains the implementations for shell commands'''
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

class CommandLogin(BaseCommand):
	'''Logs into the specified server'''
	def __init__(self):
		super().__init__()
		self.name = 'login'
		# self.help = helptext.login_cmd
		self.description = 'Logs into the specified server'
		
	def execute(self, shellstate: ShellState) -> RetVal:
		return RetVal(ErrUnimplemented)


class CommandLogout(BaseCommand):
	'''Logs out of the currently-connected server'''
	def __init__(self):
		super().__init__()
		self.name = 'login'
		# self.help = helptext.logout_cmd
		self.description = 'Logs out of the currently-connected server'
		
	def execute(self, shellstate: ShellState) -> RetVal:
		return RetVal(ErrUnimplemented)


class CommandPreregister(BaseCommand):
	'''Preregister an account for someone'''
	def __init__(self):
		super().__init__()
		self.name = 'preregister'
		self.help = helptext.preregister_cmd
		self.description = 'Preregister a new account for someone.'
		
	def execute(self, shellstate: ShellState) -> RetVal:
		if len(self.tokens) > 2 or len(self.tokens) == 0:
			print(self.help)
			return ''
		
		try:
			port = int(self.tokens[0])
		except:
			return RetVal(ErrBadValue, 'Bad port number')
		
		user_id = ''
		if len(self.tokens) == 2:
			user_id = self.tokens[1]
		
		if user_id and ('"' in user_id or '/' in user_id):
			return RetVal(ErrBadData, 'User ID may not contain " or /.')
		
		status = shellstate.client.preregister_account(port, user_id)
		
		if status['status'] != 200:
			return RetVal(ErrServerError, f"Preregistration error: {status.info()}")
		
		outparts = [ 'Preregistration success:\n' ]
		if status['uid']:
			outparts.extend(['User ID: ', status['uid'], '\n'])
		outparts.extend(['Workspace ID: ' , status['wid'], '\n',
						'Registration Code: ', status['regcode']], '\n')
		
		return RetVal(ErrOK, ''.join(outparts))


class CommandRegister(BaseCommand):
	'''Register an account on a server'''
	def __init__(self):
		super().__init__()
		self.name = 'register'
		self.help = helptext.register_cmd
		self.description = 'Register a new account on the connected server.'

	def validate(self) -> RetVal:
		if not self.tokens:
			return RetVal(ErrEmptyData, 'A server must be specified.')

		if 'password' in self.args:		
			status = check_password_complexity(self.args['password'])
			if status['strength'] in [ 'very weak', 'weak' ]:
				return RetVal(ErrBadValue, 'Unfortunately, the password you entered was too weak. '
					'Please use another.')
		
		if 'userid' in self.args:
			if not validate_userid(self.args['userid']):
				return RetVal(ErrBadValue, 'The user ID given is not valid')
		else:
			self.args['userid'] = ''

		return RetVal()

	def execute(self, shellstate: ShellState) -> RetVal:
		
		if 'password' not in self.args:
			self._setpassword_interactive()
			if 'password' not in self.args:
				return RetVal()

		status = shellstate.client.register_account(self.tokens[0], self.args['password'], 
													self.args['userid'])
		
		returncodes = {
			304:"This server does not allow self-registration.",
			406:"This server requires payment before registration can be completed.",
			101:"Registration request sent. Awaiting approval.",
			300: "Registration unsuccessful. The server had an error. Please contact technical " \
				"support for the organization for assistance. Sorry!",
			408:"This workspace already exists on the server. Registration is not needed."
		}
		
		if status.error():
			return status

		# TODO: finish handling registration
		# 1) Set friendly name for account, if applicable - SETADDR
		# 2) Upload keycard and receive signed keycard - SIGNCARD
		# 3) Save signed keycard to database
		
		return RetVal(ErrUnimplemented, 'Registration not completely implemented')

	def _setpassword_interactive(self):
		print("Please enter a passphrase. Please use at least 10 characters with a combination " \
			"of uppercase and lowercase letters and preferably a number and/or symbol. You can "
			"even use non-English letters, such as ß, ñ, Ω, and Ç! Leading and trailing spaces "
			"will be stripped.")
		
		while True:
			password = getpass("Password: ").strip()
			if not password:
				return
			
			confirmation = getpass("Confirm password: ").strip()
			if password == confirmation:
				status = check_password_complexity(password)
				if status['strength'] in [ 'very weak', 'weak' ]:
					print("Unfortunately, the password you entered was too weak. Please " \
							"use another.")
					continue
				self.args['password'] = password
				break
			else:
				print("Passwords do not match.")


class CommandRegCode(BaseCommand):
	'''Finish registration of an account with a registration code'''
	def __init__(self):
		super().__init__()
		self.name = 'regcode'
		# self.help = helptext.regcode_cmd
		self.description = 'Finish registration of an account with a registration code'
	
	def validate(self) -> RetVal:
		return super().validate()
		
	def execute(self, shellstate: ShellState) -> RetVal:
		return RetVal(ErrUnimplemented)

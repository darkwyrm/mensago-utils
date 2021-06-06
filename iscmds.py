'''Contains the implementations for shell commands'''
from getpass import getpass

from pycryptostring import CryptoString
from retval import RetVal, ErrBadData, ErrBadValue, ErrEmptyData, ErrOK, ErrServerError, \
	ErrUnimplemented

from pymensago.encryption import check_password_complexity
import pymensago.iscmds as iscmds
from pymensago.kcresolver import get_mgmt_record
from pymensago.utils import validate_userid, MAddress

import helptext
from shellbase import BaseCommand, ShellState

class CommandLogin(BaseCommand):
	'''Logs into the specified server'''
	def __init__(self):
		super().__init__()
		self.name = 'login'
		self.help = helptext.login_cmd
		self.description = 'Logs into the specified server'

	def validate(self, shellstate: ShellState) -> RetVal:
		if len(self.tokens) > 1:
			return (ErrBadValue, self.help)
		
		if len(self.tokens) == 1:
			addr = MAddress(self.tokens[0])
			if not addr.is_valid():
				return RetVal(ErrBadValue, 'Invalid address')

		status = shellstate.client.pman.get_active_profile()
		if status.error():
			return status
		
		return RetVal()
		
	def execute(self, shellstate: ShellState) -> RetVal:
		addr = MAddress()
		if len(self.tokens) == 0:
			status = shellstate.client.pman.get_active_profile()
			profile = status['profile']
			addr.set(profile.address())
		else:
			addr.set(self.tokens[0])
		
		status = shellstate.client.kcr.resolve_address(addr)
		if status.error():
			return status
		wid = status['Workspace-ID']
		status = get_mgmt_record(addr.domain)
		if status.error():
			return status
		
		orgkey = CryptoString(status['pvk'])
		status = iscmds.login(shellstate.client.conn, wid, orgkey)

		return RetVal(ErrUnimplemented)


class CommandLogout(BaseCommand):
	'''Logs out of the currently-connected server'''
	def __init__(self):
		super().__init__()
		self.name = 'logout'
		self.help = helptext.logout_cmd
		self.description = 'Logs out of the currently-connected server'
		
	def execute(self, shellstate: ShellState) -> RetVal:
		return shellstate.client.logout()


class CommandPreregister(BaseCommand):
	'''Preregister an account for someone'''
	def __init__(self):
		super().__init__()
		self.name = 'preregister'
		self.help = helptext.preregister_cmd
		self.description = 'Preregister a new account for someone.'
		
	def execute(self, shellstate: ShellState) -> RetVal:
		if len(self.tokens) > 2 or len(self.tokens) == 0:
			return RetVal(ErrBadData, self.help)
		
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

	def validate(self, shellstate: ShellState) -> RetVal:
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
			password = _setpassword_interactive()
			if not password:
				return RetVal()
			self.args['password'] = password

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

class CommandRegCode(BaseCommand):
	'''Finish registration of an account with a registration code'''
	def __init__(self):
		super().__init__()
		self.name = 'regcode'
		self.help = helptext.regcode_cmd
		self.description = 'Finish registration of an account with a registration code'
	
	def validate(self, shellstate: ShellState) -> RetVal:
		if len(self.tokens) not in [2, 3]:
			return RetVal(ErrBadData, self.help)

		addr = MAddress()
		status = addr.set(self.tokens[0])
		if status.error():
			return RetVal(ErrBadValue, 'Invalid address')
		
		if len(self.tokens) == 3:
			self.args['password'] = self.tokens[2]
		
		return RetVal()
		
	def execute(self, shellstate: ShellState) -> RetVal:
		if 'password' not in self.args:
			password = _setpassword_interactive()
			if not password:
				return RetVal()
			self.args['password'] = password
		
		
		return RetVal(ErrUnimplemented)


def _setpassword_interactive():
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
			return password
		else:
			print("Passwords do not match.")

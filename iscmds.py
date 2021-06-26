'''Contains the implementations for shell commands'''
from getpass import getpass

from pycryptostring import CryptoString
from pymensago.workspace import Workspace
from retval import ErrExists, RetVal, ErrBadData, ErrBadValue, ErrEmptyData, ErrOK, ErrServerError, \
	ErrUnimplemented

from pymensago.encryption import Password, check_password_complexity
import pymensago.iscmds as iscmds
from pymensago.kcresolver import get_mgmt_record
from pymensago.utils import MAddress, UserID, Domain

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
			addr.set(profile.wid.as_string() + '/' + profile.domain.as_string())
		else:
			addr.set(self.tokens[0])

		status = self._ensure_connection(addr.domain, shellstate)
		if status.error():
			return status

		status = shellstate.client.kcr.resolve_address(addr)
		if status.error():
			return status
		wid = status['Workspace-ID']
		status = get_mgmt_record(addr.domain.as_string())
		if status.error():
			return status
		
		orgkey = CryptoString(status['ek'])
		return iscmds.login(shellstate.client.conn, wid, orgkey)


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
		if len(self.tokens) in [0, 1]:
			return RetVal(ErrBadData, self.help)

		if not Domain(self.tokens[0]).is_valid():
			return RetVal(ErrBadValue, f"{self.tokens[0]} isn't a valid server domain")
		
		if 'password' in self.args:		
			status = check_password_complexity(self.args['password'])
			if status['strength'] in [ 'very weak', 'weak' ]:
				return RetVal(ErrBadValue, 'Unfortunately, the password you entered was too weak. '
					'Please use another.')
		
		if 'userid' in self.args:
			if not UserID(self.args['userid']).is_valid():
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

		status = shellstate.client.register_account(Domain(self.tokens[0]), self.args['password'], 
													UserID(self.args['userid']))
		
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

		# TODO: Assign name to account
		# TODO: Add an entry to the keycard
		# TODO: Save signed keycard to database
		
		return RetVal()

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

		# Check to make sure we have a profile before we do anything
		status = shellstate.client.pman.get_active_profile()
		if status.error():
			return status
		profile = status['profile']
		if profile.wid:
			return RetVal(ErrExists, 'An identity has already been assigned to this profile.')
		
		addr = MAddress()
		status = addr.set(self.tokens[0])
		if status.error():
			return RetVal(ErrBadValue, 'Invalid address')
		
		if len(self.tokens) == 3:
			self.args['password'] = self.tokens[2]
		
		return RetVal()
		
	def execute(self, shellstate: ShellState) -> RetVal:
		if 'password' not in self.args:
			pw = _setpassword_interactive()
			if not pw:
				# Allow the user to cancel this command from within the password prompt
				return RetVal()
			self.args['password'] = pw
		
		addr = MAddress(self.tokens[0])
		status = self._ensure_connection(addr.domain, shellstate)
		if status.error():
			return status
		
		status = shellstate.client.pman.get_active_profile()
		if status.error():
			return status
		profile = status['profile']

		status = shellstate.client.redeem_regcode(addr, self.tokens[1], self.args['password'])
		if status.error():
			return status

		return RetVal(ErrOK, 'Registration code redeemed successfully')


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

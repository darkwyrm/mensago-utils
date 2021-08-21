'''Contains the implementations for shell commands'''
from getpass import getpass

from retval import ErrExists, RetVal, ErrBadData, ErrBadValue, ErrOK, ErrServerError

from pymensago.contacts import delete_field, save_field, load_field, save_list_field
from pymensago.flatcontact import unflatten
from pymensago.encryption import check_password_complexity
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

		return shellstate.client.login(addr)


class CommandLogout(BaseCommand):
	'''Logs out of the currently-connected server'''
	def __init__(self):
		super().__init__()
		self.name = 'logout'
		self.help = helptext.logout_cmd
		self.description = 'Logs out of the currently-connected server'
		
	def execute(self, shellstate: ShellState) -> RetVal:
		return shellstate.client.logout()


class CommandMyInfo(BaseCommand):
	'''Manipulate workspace information'''
	def __init__(self):
		super().__init__()
		self.name = 'myinfo'
		self.help = helptext.myinfo_cmd
		self.description = 'Set workspace contact information'

	def validate(self, shellstate: ShellState) -> RetVal:
		if len(self.tokens) > 3:
			return RetVal(ErrBadData, self.help)
		
		if len(self.tokens):
			verb = self.tokens[0].casefold()
			if verb not in [ 'set', 'del', 'check', 'get' ]:
				return RetVal(ErrBadValue, "Verb must be 'set', 'get', 'del', 'check'")
		else:
			verb = 'get'
		self.args['verb'] = verb

		field = ''
		if verb == 'set' or verb == 'add':
			if len(self.tokens) != 3:
				return RetVal(ErrBadData, self.help)

			field = self.tokens[1]
			if not _is_field_valid(self.tokens[1]):
				return RetVal(ErrBadValue, f"Invalid field specifier {field}")

			if not self.tokens[2]:
				return RetVal(ErrBadValue, "Value may note be empty")
			
			self.args['field'] = field
			self.args['value'] = self.tokens[2]
		
		elif verb == 'del':
			if len(self.tokens) != 2:
				return RetVal(ErrBadData, self.help)

			field = self.tokens[1]
			if not _is_field_valid(self.tokens[1]):
				return RetVal(ErrBadValue, f"Invalid field specifier {field}")
			
			self.args['field'] = field
		
		elif verb == 'check':
			# 'check'
			if len(self.tokens) != 1:
				return RetVal(ErrBadData, self.help)
		
		elif verb == 'get':
			if len(self.tokens) == 2:
				self.args['field'] = self.tokens[1]
			else:
				self.args['field'] = '*'

		return RetVal()

	def execute(self, shellstate: ShellState) -> RetVal:

		status = shellstate.client.pman.get_active_profile()
		if not status.error():
			profile = status['profile']
		
		if self.args['verb'] == 'set':
			return profile.save_field(self.args['field'], self.args['value'])
		elif self.args['verb'] == 'del':
			return delete_field(profile.db, profile.wid, self.args['field'])
		elif self.args['verb'] == 'get':
			status = profile.load_field(self.args['field'])
			if status.error():
				return status
			
			if self.args['field'] == '*':
				out = list()
				for i in range(len(status['name'])):
					out.append(f"{status['name'][i]}: {status['value'][i]}")
				return RetVal(ErrOK, '\n'.join(out))
			
			return status.set_info(status['value'])
			
		elif self.args['verb'] == 'check':
			status = _check_myinfo(shellstate)
			if status.error():
				out = list()
				outstatus = RetVal(ErrBadData)
				if 'invalid' in status['errors']:
					out.append('The following fields were invalid:')
					out.extend(status['errors']['invalid'])
					outstatus.set_value('invalid', status['errors']['invalid'])
				
				if 'missing' in status['errors']:
					out.append('\nThe following field components were missing:')
					out.extend(status['errors']['missing'])
					outstatus.set_value('missing', status['errors']['missing'])
				
				outstatus.set_info('\n'.join(out))
				return outstatus 
			return RetVal(ErrOK, 'User contact info is compliant')

		return load_field(profile.db, profile.wid, '*')


class CommandPreregister(BaseCommand):
	'''Preregister an account for someone'''
	def __init__(self):
		super().__init__()
		self.name = 'preregister'
		self.help = helptext.preregister_cmd
		self.description = 'Preregister a new account for someone.'
		
	def validate(self, shellstate: ShellState) -> RetVal:
		if len(self.tokens) not in [1,2]:
			return RetVal(ErrBadData, self.help)
		
		if self.tokens[0].casefold() != 'none':
			uid = UserID(self.tokens[0])
			if not uid.is_valid():
				return RetVal(ErrBadData, 'Bad user ID/workspace ID')

		if len(self.tokens) == 2:
			domain = Domain(self.tokens[1])
			if not domain.is_valid():
				return RetVal(ErrBadData, 'Bad domain')

		return RetVal()
	
	def execute(self, shellstate: ShellState) -> RetVal:
		
		uid = UserID()
		if self.tokens[0].casefold() != 'none':
			uid.set(self.tokens[0])

		domain = Domain()
		if len(self.tokens) == 2:
			domain.set(self.tokens[1])

		status = shellstate.client.preregister_account(uid, domain)
		
		if status.error():
			return RetVal(ErrServerError, f"Preregistration error: "
				f"{status.error()} / {status.info()}")
		
		outparts = [ 'Preregistration success:\n' ]
		if status.has_value('uid') and status['uid']:
			outparts.extend(['User ID: ', status['uid'].as_string(), '\n'])
		outparts.extend(['Workspace ID: ' , status['wid'].as_string(), '\n',
						'Registration Code: ', status['regcode'], '\n'])
		
		# Adding the registration values to the return status permits integration testing of
		# the command
		out = RetVal(ErrOK, ''.join(outparts)).set_values({
			'wid': status['wid'],
			'regcode': status['regcode'],
			'domain': status['domain']
		})
		if status.has_value('uid') and status['uid']:
			out['uid'] = status['uid']
		return out


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

		uid = UserID(self.args['userid'])
		status = shellstate.client.register_account(Domain(self.tokens[0]), self.args['password'], 
													uid)
		
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

		status = shellstate.client.pman.get_active_profile()
		if status.error():
			return status
		profile = status['profile']
		
		if self.tokens[1].casefold() != 'none':
			parts = self.tokens[1].split(' ')
			
			if len(parts) == 1 and parts[0]:
				profile.save_field('GivenName', parts[0])
				profile.save_field('FormattedName', parts[0])
			elif len(parts) == 2:
				profile.save_field('GivenName', parts[0])
				profile.save_field('FamilyName', parts[1])
				profile.save_field('FormattedName', self.tokens[1])
			elif len(parts) > 2:
				profile.save_field('GivenName', parts[0])
				profile.save_field('FamilyName', parts[-1])
				profile.save_field('FormattedName', self.tokens[1])
				save_list_field(profile.db, profile.wid, 'AdditionalNames', parts[1:-1])
		
		workspace_data = {
				'Label':		'Primary',
				'Workspace':	profile.wid.as_string(),
				'Domain':		profile.domain.as_string(),
		}
		if not uid.is_wid():
			workspace_data['UserID'] = uid.as_string()
		profile.save_list_field('Mensago', [ workspace_data ])


		# TODO: Add an entry to the keycard
		# TODO: Save signed keycard to database
		
		return RetVal().set_info('Registration successful')


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
		if not profile.wid.is_empty():
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
			out = status
			out.set_info(f"An error occurred: {status.error()} / {status.info()}")
			return out

		workspace_data = {
				'Label':		'Primary',
				'Workspace':	profile.wid.as_string(),
				'Domain':		profile.domain.as_string(),
		}
		if not addr.id.is_wid():
			workspace_data['UserID'] = addr.id.as_string()
		profile.save_list_field('Mensago', [ workspace_data ])
		
		# TODO: Ask user for first and last name

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


_toplevel_fields = [
	'FormattedName',
	'GivenName',
	'FamilyName',
	'Prefix',
	'Gender',
	'Bio',
	'Anniversary',
	'Birthday',
	'Email',
	'Organization',
	'Title',
	'Notes',
]

_list_fields = [
	'Nicknames',
	'AdditionalNames',
	'Suffixes',
	'OrgUnits',
	'Categories',
	'Languages',
]

_dictlist_fields = {
	'Phone' : { 'Label':True, 'Value':True, 'Preferred':False },
	'Social' : { 'Label':True, 'Value':True, 'Preferred':False },
	'Messaging' : { 'Label':True, 'Value':True, 'Preferred':False },
	'Websites' : { 'Label':True, 'Value':True, 'Preferred':False },
	'Custom' : { 'Label':True, 'Value':True },
	'Mensago' : { 'Label':True, 'UserID':False, 'Workspace':True, 'Domain':True, 'Preferred':False },
	'Keys' : { 'Label':True, 'KeyType':True, 'KeyHash':True, 'Value':True},
	'MailingAddresses' : { 'Label':True, 'POBox':False, 'StreetAddress':False, 'ExtendedAddress':False,
							'Locality':False, 'Region':False, 'PostalCode':False, 'Country':False,
							'Preferred':False },
	'Photo' : { 'Mime':True, 'Data':True },
	'Attachments' : { 'Name':True, 'Mime':True, 'Data':True },
}


def _is_field_valid(fieldname: str) -> bool:
	'''Validates the field name specifier passed to MyInfo. This function is very specific to the
	Mensago contacts spec and will not permit fields outside the spec.'''

	parts = fieldname.split('.')

	if parts[0] == 'Annotations':
		parts = parts[1:]

	if len(parts) == 1:
		return parts[0] in _toplevel_fields
	
	if len(parts) == 2:
		try:
			_ = int(parts[1])
		except:
			return False
		return parts[0] in _list_fields

	if len(parts) == 3:
		try:
			_ = int(parts[1])
		except:
			return False
		
		return parts[0] in _dictlist_fields and parts[2] in _dictlist_fields[parts[0]].keys()

	return False


def _check_myinfo(shellstate: ShellState) -> RetVal:
	'''This function performs a complete check of the userinfo stored in the database and confirms 
	that it complies with the spec.'''
	
	status = shellstate.client.pman.get_active_profile()
	if not status.error():
		profile = status['profile']
	status = load_field(profile.db, profile.wid, '*')
	if status.error():
		return status

	errors = dict()

	# Check validity of all fields
	for field in status['name']:
		if not _is_field_valid(field):
			if 'invalid' not in errors:
				errors['invalid'] = list()
			errors['invalid'].append(field)
	
	# Check for required values. If we got this far, then all field names are valid. We just need
	# to ensure that subfields that are required exist.
	# Merge the values into a dictionary so we can unflatten and verify	
	flatcontact = dict()
	for i in range(len(status['name'])):
		flatcontact[status['name'][i]] = status['value'][i]
	status.empty()
	status = unflatten(flatcontact)
	if status.error():
		return status
	
	contact = status['value']

	for toplevel in _dictlist_fields.keys():
		
		# Checks only matter if the field itself exists in the contact
		if toplevel in contact:

			# The field exists in the contact, so we will check to ensure that each required field
			# in the spec for the entry actually exists
			for item in contact[toplevel]:
				for key in _dictlist_fields[toplevel].keys():
					# Each item is true if it is required
					if _dictlist_fields[toplevel][key] and key not in item:
						if 'missing' not in errors:
							errors['missing'] = list()
						errors['missing'].append(f'{key} missing from {toplevel} item')

	if len(errors):
		return RetVal(ErrBadData).set_value('errors', errors)
	
	return RetVal()

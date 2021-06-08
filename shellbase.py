'''Provides the command processing API'''
# pylint: disable=unused-argument

from glob import glob
import os
import re

from pymensago.client import MensagoClient
from retval import ErrBadType, ErrBadValue, RetVal

# This global is needed for meta commands, such as Help. Do not access this list directly unless
# there is literally no other option.
gShellCommands = dict()

class ShellState:
	'''Stores the state of the shell'''
	def __init__(self):
		self.pwd = os.getcwd()
		if 'OLDPWD' in os.environ:
			self.oldpwd = os.environ['OLDPWD']
		else:
			self.oldpwd = ''
		
		self.aliases = dict()
		self.client = MensagoClient()


class BaseCommand:
	'''The main base Command class. Defines the basic API and all tagsh commands inherit from it.'''

	def __init__(self):

		self.name = ''
		self.help = ''
		self.description = ''

		# Argument-handling attributes
		self.rawcmd = ''

		# Contains an ordered list of raw tokens. This makes commands simple commands which only
		# have an optional argument or a fixed list of arguments easy to write.
		self.tokens = list()

		# Named arguments. More complex commands can use this to have multiple optional arguments
		# where order doesn't matter. The two can even be mixed, but all named arguments need to be
		# placed after the ordered ones because they are removed from the token list.
		#
		# `cmd foo bar spam=eggs` -> self.tokens = ['foo', 'bar'], self.args = ['spam':'eggs']
		#
		# Named arguments which need quoting should have quotes around the entire thing:
		# `cmd foo "bar=spam eggs"`
		self.args = dict()

		self.splitter = re.compile(r'\"(?:\%\"|[^\"])*\"|\"[^\"]*\"|[^\s\"]+')

	def set(self, command: str) -> RetVal:
		'''Sets the input and does some basic validation. This method expects the entire raw 
		command, including the command name.'''

		if not command:
			self.args = dict()
		
		if not isinstance(command, str):
			return RetVal(ErrBadType, 'command not a string')
		
		self.rawcmd = command
			
		return self._tokenize()
	
	def validate(self, shellstate: ShellState) -> RetVal:
		'''A hook function implemented by child classes to validate input from the command line 
		so that execute() only need be concerned with performing the requested action. It is called 
		once the raw command line is tokenized. The value returned is sent directly to the main 
		event loop -- any validation errors can be placed in the return value's info field.'''
		return RetVal()

	def get_aliases(self):
		'''Returns a dictionary of alternative names for the command'''

		return dict()
	
	def execute(self, shellstate: ShellState) -> RetVal:
		'''The base class purposely does nothing. To be implemented by subclasses'''

		return ''
	
	def autocomplete(self, ptokens: list, shellstate: ShellState) -> list:
		'''Subclasses implement whatever is needed for their specific case. ptokens 
contains all tokens from the raw input except the name of the command. All 
double quotes have been stripped. Subclasses are expected to return a list 
containing matches.'''

		return list()

	def _ensure_connection(self, domain: str, shellstate: ShellState) -> RetVal:
		'''Ensures that the client is connected to a server'''
		if shellstate.client.conn.is_connected():
			return RetVal()
		
		return shellstate.client.connect(domain)

	def _tokenize(self) -> RetVal:
		'''Takes the raw command line passed to it, splits it into an ordered list of tokens, and 
		places them in self.tokens. This method handles double-quotes for encapsulating arguments 
		and escaping a quotation mark within them using a %, i.e. `cmd "foo %"bar%""` yields the 
		tokens `cmd` and `foo "bar"`. '''
		raw_tokens = re.findall(self.splitter, self.rawcmd.strip())
		if raw_tokens:
			del raw_tokens[0]
		
		self.tokens = list()
		for i in range(len(raw_tokens)):
			token = raw_tokens[i].strip('"').replace('%"','"')
			if '=' in token:
				parts = token.split('=', 1)
				# A token like `=foo` will not be treated as a key=value pair.
				if parts[0]:
					self.args[parts[0]] = parts[1]
					continue
			
			self.tokens.append(token)

		return RetVal()


class FilespecBaseCommand(BaseCommand):
	'''Many commands operate on a list of file specifiers'''
	def __init__(self, raw_input=None, ptoken_list=None):
		super().__init__(self,raw_input,ptoken_list)
		self.name = 'FilespecBaseCommand'
		
	def process_wildcards(self, tokens: list) -> list:
		'''Converts a list containing filenames and/or wildcards into a list of file paths.'''

		out = list()
		for index in tokens:
			item = index
			
			if item[0] == '~':
				item = item.replace('~', os.getenv('HOME'))
			
			if os.path.isdir(item):
				if item[-1] == '/':
					item = item + "*.*"
				else:
					item = item + "/*.*"
			try:
				if '*' in item:
					result = glob(item)
					out.extend(result)
				else:
					out.append(item)
			except:
				continue
		return out


def get_filespec_completions(token: str):
	'''Implements autocompletion for commands which take a filespec. This be a directory, filename, 
	or wildcard. If a wildcard, this method returns no results.'''

	if not token or '*' in token:
		return list()
	
	outData = list()
	
	quoteMode = bool(token[0] == '"')
	
	if quoteMode:
		items = glob(token[1:] + '*')
	else:
		items = glob(token + '*')
	
	for item in items:
		display = item
		if quoteMode or ' ' in item:
			data = '"' + item + '"'
		else:
			data = item
		
		if os.path.isdir(item):
			data = data + '/'
			display = display + '/'
		
		outData.append([data,display])
			
	return outData

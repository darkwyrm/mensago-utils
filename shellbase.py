'''Provides the command processing API'''
# pylint: disable=unused-argument

from glob import glob
import os
import re

from pymensago.client import MensagoClient
from retval import ErrBadType, RetVal

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
		self.tokens = list()
	
	def set(self, tokens: list) -> RetVal:
		'''Sets the input and does some basic validation'''

		if not tokens:
			self.tokens = list()
		
		if not isinstance(tokens, list):
			return RetVal(ErrBadType, 'command tokens not a list')
		
		self.tokens = tokens
				
		return RetVal()
	
	def get_aliases(self):
		'''Returns a dictionary of alternative names for the command'''

		return dict()
	
	def execute(self, pshell_state: ShellState) -> RetVal:
		'''The base class purposely does nothing. To be implemented by subclasses'''

		return ''
	
	def autocomplete(self, ptokens: list, pshell_state: ShellState) -> list:
		'''Subclasses implement whatever is needed for their specific case. ptokens 
contains all tokens from the raw input except the name of the command. All 
double quotes have been stripped. Subclasses are expected to return a list 
containing matches.'''

		return list()


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

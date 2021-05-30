'''Provides the command processing API'''
# pylint: disable=unused-argument

from glob import glob
import os
import re

from pymensago.client import MensagoClient
from retval import RetVal

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
		self.tokenList = list()
	
	def set(self, tokens: list) -> RetVal:
		'''Sets the input and does some basic validation'''

		if tokens:
			self.tokenList = tokens[1:]
		else:
			self.tokenList = list()
		
		return RetVal()
	
	def get_aliases(self):
		'''Returns a dictionary of alternative names for the command'''

		return dict()
	
	def is_valid(self):
		'''Subclasses validate their information and return an error string'''

		return ''
	
	def execute(self, pshell_state):
		'''The base class purposely does nothing. To be implemented by subclasses'''

		return ''
	
	def autocomplete(self, ptokens, pshell_state):
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
		
	def ProcessFileList(self, ptoken_list):
		'''Converts a list containing filenames and/or wildcards into a list of file paths.'''

		fileList = list()
		for index in ptoken_list:
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
					fileList.extend(result)
				else:
					fileList.append(item)
			except:
				continue
		return fileList


def GetFileSpecCompletions(pFileToken):
	'''Implements autocompletion for commands which take a filespec. This be a directory, filename, 
	or wildcard. If a wildcard, this method returns no results.'''

	if not pFileToken or '*' in pFileToken:
		return list()
	
	outData = list()
	
	quoteMode = bool(pFileToken[0] == '"')
	
	if quoteMode:
		items = glob(pFileToken[1:] + '*')
	else:
		items = glob(pFileToken + '*')
	
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

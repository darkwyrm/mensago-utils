#!/usr/bin/env python3
'''This is the main module'''

import re

from prompt_toolkit import HTML
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion, ThreadedCompleter
from prompt_toolkit.shortcuts.utils import print_formatted_text

from commandaccess import init_commands, get_command, get_command_names
from shellbase import ShellState

class ShellCompleter(Completer):
	'''Class for handling command autocomplete'''
	def __init__(self, pshell_state):
		Completer.__init__(self)
		self.lexer = re.compile(r'"[^"]+"|"[^"]+$|[\S\[\]]+')
		self.shell = pshell_state

	def get_completions(self, document, complete_event):
		tokens = self.lexer.findall(document.current_line_before_cursor.strip())
		
		if len(tokens) == 1:
			commandToken = tokens[0]

			# We have only one token, which is the command name
			names = get_command_names()
			for name in names:
				if name.startswith(commandToken):
					yield Completion(name[len(commandToken):],display=name)
		elif tokens:
			cmd = get_command(tokens[0])
			if cmd.name != 'unrecognized' and tokens:
				outTokens = cmd.autocomplete(tokens[1:], self.shell)
				for out in outTokens:
					yield Completion(out,display=out,
							start_position=-len(tokens[-1]))
		

class Shell:
	'''The main shell class for the application.'''
	def __init__(self):
		init_commands()
		self.state = ShellState()
		
		self.lexer = re.compile(r'"[^"]+"|\S+')

	def Prompt(self):
		'''Begins the prompt loop.'''
		session = PromptSession()
		commandCompleter = ThreadedCompleter(ShellCompleter(self.state))
		
		split_pattern = re.compile(r'\"(?:\%\"|[^\"])*\"|\"[^\"]*\"|[^\s\"]+')

		while True:
			try:
				raw_input = session.prompt(HTML('🐧<yellow><b> > </b></yellow>' ),
										completer=commandCompleter)
			except KeyboardInterrupt:
				break
			except EOFError:
				break
			else:
				raw_tokens = re.findall(split_pattern, raw_input.strip())
				
				tokens = list()
				for token in raw_tokens:
					tokens.append(token.strip('"').replace('%"','"'))

				if not tokens:
					continue
				
				cmd = get_command(tokens[0])
				status = cmd.set(tokens[1:])
				if status.error():
					print(f"BUG: error setting info for command: {status.error()} / " +
							f"{status.info()}")
					break

				status = cmd.execute(self.state)
				if status.info():
					print_formatted_text(status.info())


if __name__ == '__main__':
	Shell().Prompt()

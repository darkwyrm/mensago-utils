'''This module contains code for the in-app help system. It's simple, but intended to be expandable 
and actually useful'''

_gHelpTopics = dict()
_gKeywordMap = dict()


def addtopic(topic: str, text: str, keywords: list):
	'''Adds a topic to the help database. The list of keywords may be None, but its usage is 
	highly encouraged.'''
	# TODO: Implement help.addtopic()
	pass

def gettopic(topic: str) -> str:
	'''Gets a help topic. If it doesn't exist, a list of topics which contain keywords for the 
	topic requested is returned.'''
	global _gHelpTopics, _gKeywordMap

	t = topic.casefold()
	if t in _gHelpTopics:
		return _gHelpTopics[t]
	
	if t in _gKeywordMap:
		out = [ f"No topics were found matching the keyword {topic}. However, the following topics "
			"include it as a keyword."]
		out.extend(_gKeywordMap[t])
		return '\n'.join(out)
	
	return f"No help found for the topic {topic}"


def gettopiclist() -> list:
	'''Gets the list of available topics in the help database'''
	global _gHelpTopics
	return _gHelpTopics.keys()

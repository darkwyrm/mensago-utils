import shellbase

def test_parsing():
	'''Tests the baseline command parsing in BaseCommand'''
	
	cmd = shellbase.BaseCommand()

	# Subtest #1: Basic arguments
	status = cmd.set('cmd foo bar baz')
	assert not status.error(), 'test_parsing: #1 failed to tokenize basic arguments'
	assert len(cmd.tokens) == 3, 'test_parsing: #1 had wrong token count'

	# Subtest #2: Quote handling
	status = cmd.set('cmd foo "bar baz"')
	assert not status.error(), 'test_parsing: #2 failed to tokenize quoted arguments'
	assert len(cmd.tokens) == 2, 'test_parsing: #2 had wrong token count'

	# Subtest #3: Escape handling
	status = cmd.set('cmd foo "bar %"baz%" "')
	assert not status.error(), 'test_parsing: #3 failed to tokenize quoted arguments'
	assert len(cmd.tokens) == 2, 'test_parsing: #3 had wrong token count'
	assert cmd.tokens[1] == 'bar "baz" ', 'test_parsing: #3 failed to handle quote escaping'

	# Subtest #4: Named arguments
	status = cmd.set('cmd foo bar=baz')
	assert not status.error(), 'test_parsing: #4 failed to parse tokenize arguments'
	assert len(cmd.tokens) == 1, 'test_parsing: #4 had wrong token count'
	assert 'bar' in cmd.args and cmd.args['bar'] == 'baz', \
		'test_parsing: #4 failed to parse named arguments'

	# Subtest #5: Quoted named arguments
	status = cmd.set('cmd foo "bar=spam eggs"')
	assert not status.error(), 'test_parsing: #5 failed to parse tokenize arguments'
	assert len(cmd.tokens) == 1, 'test_parsing: #5 had wrong token count'
	assert 'bar' in cmd.args and cmd.args['bar'] == 'spam eggs', \
		'test_parsing: #5 failed to parse named arguments'


if __name__ == '__main__':
	test_parsing()

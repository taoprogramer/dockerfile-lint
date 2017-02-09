import re

token_whitespace = re.compile(r'[\t\v\f\r ]+')
token_escape_command = re.compile(r'^#[ \t]*escape[ \t]*=[ \t]*(?P<escapechar>.).*$')
token_comment = re.compile(r'^#.*$')



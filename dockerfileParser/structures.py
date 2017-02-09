import re


class DockerfileNotStringArray(Exception):
    pass


class Node(object):
    def __init__(self, value=None, next_node=None, children=None, attributes=None, original=None, flags="",
                 start_line=None, end_line=None):
        self.value = value
        self.next_node = next_node
        self.children = children or []
        self.attributes = attributes
        self.original = original
        self.flags = flags
        self.start_line = start_line
        self.end_line = end_line

    def dump(self):
        res = []
        line = []
        if self.value:
            line.append(self.value)

        if len(self.flags):
            line.append(self.flags)

        for ch in self.children:
            res.extend(ch.dump())

        sib = self.next_node
        while sib:
            if len(sib.children):
                res.extend(sib.dump())
            elif sib.value:
                line.append(sib.value)

            sib = sib.next_node
        if line:
            res.append(line)

        return res


class Directive(object):
    default_escape_token = '\\'

    def __init__(self, line_continuation_regex=None, looking_for_directives=None, escape_seen=None):
        self.line_continuation_regex = line_continuation_regex
        self.looking_for_directives = looking_for_directives
        self.escape_seen = escape_seen
        self._escape_token = None

    @property
    def escape_token(self):
        return self._escape_token

    @escape_token.setter
    def escape_token(self, value):
        if value != '`' and value != '\\':
            raise Exception("invalid ESCAPE '%s'. Must be ` or \\" % value)

        self._escape_token = value
        self.line_continuation_regex = re.compile(r"\\[\t]*$")

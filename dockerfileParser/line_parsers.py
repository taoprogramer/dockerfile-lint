import json
from regexp import *
from structures import Node, DockerfileNotStringArray


# parse functions
def parse_ignore(rest, directive):
    return Node(), None


def parse_sub_command(rest):
    if not rest:
        return None, None


def parse_words(rest, directive):
    in_spaces, in_word, in_quote = 0, 1, 2
    words = []
    phase = in_spaces
    word = ''
    quote = '\000'
    blank = False

    ch, ch_width = "", 1
    pos = 0
    while pos <= len(rest):
        if pos != len(rest):
            ch = rest[pos]

        if phase == in_spaces:
            if pos == len(rest):
                break
            if ch.isspace():
                pos += 1
                continue
            phase = in_word

        if (phase == in_word or phase == in_quote) and pos == len(rest):
            if blank or len(word) > 0:
                words.append(word)
            break

        if phase == in_word:
            if ch.isspace():
                phase = in_spaces
                if blank or len(word):
                    words.append(word)
                word = ""
                blank = False
                pos += 1
                continue

            if ch == '\'' or ch == '"':
                quote = ch
                blank = True
                phase = in_quote

            if ch == directive.escape_token:
                if pos + ch_width == len(rest):
                    pos += 1
                    continue

                word += ch
                pos += ch_width
                ch = rest[pos]

            word += ch
            pos += 1
            continue

        if phase == in_quote:
            if ch == quote:
                phase = in_word

            if ch == directive.escape_token and quote != '\'':
                if pos + ch_width == len(rest):
                    phase = in_word
                    pos += 1
                    continue

                pos += ch_width
                word += ch
                ch = rest[pos]

            word += ch
        pos += ch

    return words


def parse_name_val(rest, key, directive):
    words = parse_words(rest, directive)
    if not len(words):
        return None, None

    rootnode = None

    if "=" not in words[0]:
        node = Node()
        rootnode = node
        strs = re.split(token_whitespace, rest, 2)

        if len(strs) < 2:
            raise Exception('must have two arguments')

        node.value = strs[0]
        node.next_node = Node()
        node.next_node.value = strs[1]

    else:
        prevnode = Node()
        for i in range(len(words)):
            if "=" not in words[i]:
                raise Exception("Syntax error - can't find = in %s. Must be of the form: name=value" % words[i])
            parts = words[i].split("=", 2)

            name = Node()
            value = Node()
            name.next_node = value
            name.value = parts[0]
            value.value = parts[1]
            if i == 0:
                rootnode = name
            else:
                prevnode.next_node = name

            prevnode = value

    return rootnode, None


def parse_env(rest, directive):
    return parse_name_val(rest, "ENV", directive)


def parse_label(rest, directive):
    return parse_name_val(rest, "LABEL", directive)


def parse_name_or_nameval(rest, directive):
    words = parse_words(rest, directive)

    if not len(words):
        return None, None

    rootnode = Node()
    prevnode = Node()

    for i in range(len(words)):
        node = Node()
        node.value = words[i]
        if i == 0:
            rootnode = node
        else:
            prevnode.next_node = node

        prevnode = node

    return rootnode, None


def parse_strings_whitespace_delimited(rest, directive):
    if not rest:
        return None, None

    node = Node()
    rootnode, prevnode = node, node

    for s in re.split(token_whitespace, rest, -1):
        prevnode = node
        node.value = s
        node.next_node = Node()
        node = node.next_node

    prevnode.next_node = None

    return rootnode, None


def parse_string(rest, directive):
    if not rest:
        return None, None

    node = Node()
    node.value = rest
    return node, None


def parse_json(rest, directive):
    rest = rest.lstrip()
    if not rest.startswith("["):
        raise ValueError

    jsons = json.loads(rest)

    top, prev = Node(), Node()
    for s in jsons:
        if not isinstance(s, str):
            raise DockerfileNotStringArray()

        node = Node(value=s)
        if not prev:
            top = node
        else:
            prev.next_node = node

        prev = node

    return top, {'json': True}


def parse_maybe_json(rest, directive):
    if not rest:
        return None, None

    try:
        node, attrs = parse_json(rest, directive)

    except DockerfileNotStringArray:
        return None, None

    except ValueError:
        node = Node()
        node.value = rest
        return node, None
    else:
        return node, attrs


def parse_maybe_json_to_list(rest, directive):
    try:
        node, attrs = parse_json(rest, directive)
    except DockerfileNotStringArray:
        raise Exception()
    except:
        return parse_strings_whitespace_delimited(rest, directive)
    else:
        return node, attrs


def parse_health_config(rest, directive):
    sep = 0
    while sep < len(rest):
        if rest[sep].isspace():
            break
    sep += 1

    next_ = sep
    while next_ < len(rest):
        if not rest[next_].isspace():
            break
        next_ += 1

    if sep == 0:
        return None, None

    typ = rest[:sep]
    cmd, attrs = parse_maybe_json(rest[next_:], directive)

    return Node(value=typ, next_node=cmd), attrs

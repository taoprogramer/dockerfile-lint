from regexp import *
from parser import dispatch
from line_parsers import parse_ignore


# helper functions
def full_dispatch(cmd, args, directive):
    fn = dispatch.get(cmd, None)
    if not fn:
        fn = parse_ignore

    sexp, attrs = fn(args, directive)

    return sexp, attrs


def split_command(line):
    args = ""
    flags = []

    cmdline = token_whitespace.split(line.strip(), 1)
    cmd = cmdline[0].lower()

    if len(cmdline) == 2:
        args, flags = extract_builder_flags(cmdline[1])

    return cmd, flags, args.strip()


def strip_comments(line):
    if token_comment.match(line):
        return ""

    return line


def extract_builder_flags(line):
    in_spaces, in_word, in_quote = 0, 1, 2

    words = []
    phase = in_spaces
    word = ""
    quote = '\000'
    blank = False
    ch = ""

    pos = 0
    while pos < len(line):
        if pos != len(line):
            ch = line[pos]

        if phase == in_spaces:
            if pos == len(line):
                break
            if ch.isspace():
                continue

            if ch != '-' or pos + 1 == len(line) or line[pos + 1] != '-':
                return line[pos:], words

        if (phase == in_word or phase == in_quote) and pos == len(line):
            if word != "--" and (blank or len(word) > 0):
                words.append(word)
            break

        if phase == in_word:
            if ch.isspace():
                phase = in_spaces
                if word == '--':
                    return line[pos:], words
                if blank or len(word) > 0:
                    words.append(word)

                word = ""
                blank = False
                continue

            if ch == '\'' or ch == '"':
                quote = ch
                blank = True
                phase = in_quote
                continue

            if ch == "\\":
                if pos + 1 == len(line):
                    continue
                pos += 1
                ch = line[pos]

            word += ch
            continue

        if phase == in_quote:
            if ch == quote:
                phase = in_word
                continue
            if ch == '\\':
                if pos + 1 == len(line):
                    phase = in_word
                    continue
                pos += 1
                ch = line[pos]

            word += ch

        print 1

        pos += 1
    return "", words

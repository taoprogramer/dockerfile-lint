from StringIO import StringIO
from command import *
from utils import *
from line_parsers import *
from structures import Directive
from rules import validate

dispatch = {
    Add: parse_json,
    Arg: parse_name_or_nameval,
    Cmd: parse_maybe_json,
    Copy: parse_maybe_json_to_list,
    Entrypoint: parse_maybe_json,
    Env: parse_env,
    Expose: parse_strings_whitespace_delimited,
    From: parse_string,
    Healthcheck: parse_health_config,
    Label: parse_label,
    Maintainer: parse_string,
    Onbuild: parse_sub_command,
    Run: parse_maybe_json,
    Shell: parse_maybe_json,
    StopSignal: parse_string,
    User: parse_string,
    Volume: parse_maybe_json_to_list,
    Workdir: parse_string

}


def parse_line(line, directive, ignore_cont):
    if directive.looking_for_directives:
        tec_match = token_escape_command.findall(line.lower())
        if len(tec_match):
            if directive.escape_seen:
                raise Exception("only one escape parser directive can be used")

            for i in range(len(token_escape_command.groups)):
                if token_escape_command.groups[i] == 'escapechar':
                    directive.escape_token = tec_match[i]
                    directive.escape_seen = True
                    return "", None

    directive.looking_for_directives = False
    if strip_comments(line) == "":
        return "", None

    if not ignore_cont and directive.line_continuation_regex.search(line):
        line = directive.line_continuation_regex.sub("", line)
        return line.strip(), None

    cmd, flags, args = split_command(line)

    node = Node()
    node.value = cmd

    sexp, attrs = full_dispatch(cmd, args, directive)

    node.next_node = sexp
    node.attributes = attrs
    node.original = line
    node.flags = flags

    return "", node


def parse(s, directive):
    if not isinstance(s, (StringIO, file)):
        raise Exception('expect StringIO or file')

    current_line = 0
    root = Node()
    root.start_line = -1

    it = iter(s.readlines())
    while True:
        try:
            line = next(it)
        except StopIteration:
            break

        scanned_line = line.lstrip()
        current_line += 1
        line, child = parse_line(scanned_line, directive, False)
        start_line = current_line

        if line and not child:
            for newline in it:
                current_line += 1

                if strip_comments(newline.strip()) == "":
                    continue

                line, child = parse_line(line + newline, directive, False)
                if child:
                    break

            if not child and line:
                _, child = parse_line(line, d, True)

        if child:
            child.start_line = start_line
            child.end_line = current_line

            if root.start_line < 0:
                root.start_line = current_line

            root.end_line = current_line
            root.children.append(child)

    return root


if __name__ == '__main__':
    d = Directive(looking_for_directives=True)
    d.escape_token = Directive.default_escape_token
    s = file('df')
    # s = StringIO("FROM	ubuntu:14.04\nMAINTAINER WDW\nCMD")

    node = parse(s, d)

    errors = validate(node.dump())
    for err in errors:
        print err.fatal, err.msg

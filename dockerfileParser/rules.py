from command import *

commands = [
    Add,
    Arg,
    Cmd,
    Copy,
    Entrypoint,
    Env,
    Expose,
    From,
    Healthcheck,
    Label,
    Maintainer,
    Onbuild,
    Run,
    Shell,
    StopSignal,
    User,
    Volume,
    Workdir
]


class Error:
    def __init__(self, msg, fatal=False):
        self._msg = msg
        self._fatal = fatal

    @property
    def msg(self):
        return self._msg

    @property
    def fatal(self):
        return self._fatal


def validate_common(errors, df):
    has_from = False
    has_maintainer = False
    has_add = False

    cmds = 0
    entries = 0

    for line in df:
        cmd, args = line[0], line[1:] if len(line) > 1 else []

        if cmd not in commands:
            errors.append(Error('unknown dockerfile instruction:%s' % cmd, True))
        if cmd == From:
            has_from = True
        if cmd == Maintainer:
            has_maintainer = True
        if cmd == Add:
            has_add = True
        if cmd == Cmd:
            cmds += 1
        if cmd == Entrypoint:
            entries += 1

    if not has_from:
        errors.append(Error('FROM instruction not found', True))
    if not has_maintainer:
        errors.append(Error('MAINTAINER instruction not found'))
    if has_add:
        errors.append(Error('use COPY instead of ADD for files and folders'))
    if cmds > 1:
        errors.append(Error('multiple CMD instructions found'))
    if entries > 1:
        errors.append(Error('multiple ENTRYPOINT instructions found'))
    if not cmds and not entries:
        errors.append(Error('neither ENTRYPOINT nor CMD instruction found'))

    return errors


validate_fn = [
    validate_common
]


def validate(df):
    errors = []
    [fn(errors, df) for fn in validate_fn]
    return errors

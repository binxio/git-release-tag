import click
import re
from collections import OrderedDict
from git_release_tag.release_info import ReleaseInfo


class SemVer(click.ParamType):
    """
    a semantic version in the form of major.minor.patch
    """

    name = "semver"

    def convert(self, value, param, ctx) -> str:
        if value is None:
            return value

        m = re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", value)
        if not m:
            self.fail(f'could not parse "{value}" as release')

        return value


class PreTagCommand(click.ParamType):
    """
    a shell command containing references to @@RELEASE@@, @@TAG@@ or @@BASE_TAG@@
    """

    name = "pre_tag_command"

    def convert(self, value, param, ctx) -> str:
        if not value is None:
            return value

        allowed = set(["RELEASE", "TAG", "BASE_TAG"])
        refs = set(re.findall(r"@@([a-zA-Z_]+)@@", value))
        unsupported = refs.difference(allowed)
        if unsupported:
            self.fail(f"found unsupported references {unsupported}")
        if "RELEASE" not in refs:
            self.fail(f"expected at least a @@RELEASE@@ reference in pre tag command")

        return value


class ReleaseLevel(click.Choice):
    """
    release level patch, minor or major
    """

    name = "release-level"

    def __init__(self):
        super(ReleaseLevel, self).__init__(["patch", "minor", "major"])

    def convert(self, value, param, ctx) -> str:
        result = super(ReleaseLevel, self).convert(value, param, ctx)
        levels = {
            "major": ReleaseInfo.MAJOR,
            "minor": ReleaseInfo.MINOR,
            "patch": ReleaseInfo.PATCH,
        }

        return levels.get(result)


class OrderedGroup(click.Group):
    def __init__(self, name=None, commands=None, **attrs):
        super(OrderedGroup, self).__init__(name, commands, **attrs)
        #: the registered subcommands by their exported names.
        self.commands = commands or OrderedDict()

    def list_commands(self, ctx):
        return self.commands

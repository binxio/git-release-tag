import click
import re
from git_release_tag.component import ReleaseInfo


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
        if value is None:
            return value

        allowed = set("RELEASE", "TAG", "BASE_TAG")
        refs = set(re.findall(r"@@([a-zA-Z_]+)@@", value))
        unsupported = refs.difference(allowed)
        if unsupported:
            self.fail(f"found unsupported references {unsupported}")
        if "RELEASE" not in refs:
            self.fail(f"expected at least a @@RELEASE@@ reference in pre tag command")

        return value


class ReleaseLevel(click.ParamType):
    """
    release level patch, minor or major
    """

    name = "release-level"

    def convert(self, value, param, ctx) -> str:
        levels = {
            "major": ReleaseInfo.MAJOR,
            "minor": ReleaseInfo.MINOR,
            "patch": ReleaseInfo.PATCH,
        }

        if levels.get(value):
            return levels.get(value)

        self.fail(f"invalid release level {value}, either major, minor or patch")

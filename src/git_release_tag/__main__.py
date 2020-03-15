import logging
import os
import click
from collections import OrderedDict
from typing import List,Optional


from git_release_tag.click_parameter_types import SemVer, PreTagCommand, ReleaseLevel, OrderedGroup
from git_release_tag.release_info import ReleaseInfo
from git_release_tag.logger import log


@click.group(cls=OrderedGroup)
@click.option("--dry-run", is_flag=True, default=False, help="do not change anything")
@click.option("--verbose", is_flag=True, default=False, help="output")
@click.pass_context
def main(ctx, dry_run, verbose):
    """
    semantic version tag support for components in git repositories.
    """
    if verbose:
        log.setLevel(logging.DEBUG)
    ctx.obj = ctx.params


@main.command()
@click.option(
    "--initial-release",
    type=SemVer(),
    default="0.0.0",
    required=False,
    help="initial version",
)
@click.option(
    "--tag-prefix", type=str, required=False, help="for the semver tag"
)
@click.option(
    "--pre-tag-command",
    type=PreTagCommand(),
    default="",
    required=False,
    help="to run before version is set and tag is made",
)
@click.argument(
    "directory", type=click.Path(file_okay=False, exists=True), required=True, nargs=-1
)
@click.pass_context
def initialize(ctx, initial_release, tag_prefix, pre_tag_command, directory):
    """
    directory with release configuration.

    Creates a release configuration using the specified `initial-release`, `tag-prefix`, and
    `pre-tag-command`. the file is called .release and has the following syntax:

    \b
        release=<initial-release>
        tag=<tag-prefix><initial-release>
        pre-tag-command=<pre-tag-command>

    The `pre-tag-command` is executed and any outstanding changes are committed and tagged with
    the specified `tag`.

    The directories must be in a git workspace.
    """

    print(f'>{pre_tag_command}<')
    directories = sorted(directory, key=lambda p: len(os.path.abspath(p).split("/")), reverse=True)

    prefixes = list(map(lambda d: os.path.basename(os.path.abspath(d)), directories))
    if tag_prefix is not None and len(directories) > 1:
        log.error('you cannot specify the same tag-prefix for different directories')
        exit(1)

    if len(set(prefixes)) != len(prefixes):
        log.error('base directory names must be unique in order to avoid non unique tag-prefixes')
        exit(1)

    for path in directories:
        component = ReleaseInfo(path)
        if not component.is_inside_work_tree:
            log.error('%s is not inside a git workspace, please run git init', path)
            exit(1)


    result = True
    for path in directories:
        result = ReleaseInfo.initialize(
            path,
            semver=initial_release,
            base_tag=tag_prefix if tag_prefix is not None else f'{os.path.basename(os.path.abspath(path))}-',
            pre_tag_command=pre_tag_command,
            dry_run=ctx.obj["dry_run"],
        ) and result

    exit(not result)


@main.command("show")
@click.option("--recursive", "-r", is_flag=True, default=False, help="all directories")
@click.option("--with-tags", is_flag=True, default=False, help="of the latest release")
@click.argument(
    "directory", type=click.Path(file_okay=False, exists=True), required=False, nargs=-1
)
@click.pass_context
def show(ctx, recursive, with_tags, directory):
    """
    current release version.

    If a single directory is specified, it will print out the current release version in the
    form of `<release>[<-sha-commit>[-dirty]]`. If multiple directories are specified, it will print out the
    directory name followed by the release version.
    """
    release_infos = ReleaseInfo.find_all(directory, recursive, ctx.obj["dry_run"])
    for release_info in release_infos:
        if not release_info.has_release_configuration:
            log.error(f"directory {release_info.directory} has no release configuration")
            exit(1)

        if recursive:
            if with_tags:
                print(f'{release_info.directory}\t{release_info.current_version}\t{release_info.tag}')
            else:
                print(f'{release_info.directory}\t{release_info.current_version}')
        else:
            print(release_info.current_version)

@main.command("bump")
@click.option("--recursive", "-r", is_flag=True, default=False, help="all directories")
@click.option("--level", type=ReleaseLevel(), required=True, help="to bump")
@click.option("--force", is_flag=True, default=False, help="even if there are no changes")
@click.argument(
    "directory", type=click.Path(file_okay=False, exists=True), required=False, nargs=-1
)
@click.pass_context
def bump(ctx, recursive:bool, force:bool, level:int, directory):
    """
    semantic version and tags the commit.

    It either bumps the major, minor or the level of the semantic version and tag the commit.
    `--force` will update the semantic version, even if there are no changes since the previous release.

    The `pre-tag-command` is executed and any outstanding changes are committed and tagged with
    the specified `tag`.
    """
    release_infos = ReleaseInfo.find_all(directory, recursive, ctx.obj["dry_run"])

    if not ReleaseInfo.validate(release_infos):
        exit(1)

    for release_info in release_infos:
        release_info.tag_next_release(level, force=force)


@main.command("validate")
@click.option("--recursive/--no-recursive", "-r", is_flag=True, default=False, help="all directories")
@click.argument(
    "directory", type=click.Path(file_okay=False, exists=True), required=False, nargs=-1
)
@click.pass_context
def validate(ctx, recursive:bool, directory):
    """
    integrity of release configuration.

    checks whether the specified directories use a unique tag prefix and
    whether the specified tag exists in the git repository.
    """
    release_infos = ReleaseInfo.find_all(directory, recursive, True)
    if ReleaseInfo.validate(release_infos):
        logging.info("ok")
    else:
        exit(1)




if __name__ == "__main__":
    main()

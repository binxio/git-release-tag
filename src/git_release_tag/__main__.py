import logging
import os
import click
from typing import List


from git_release_tag.click_parameter_types import SemVer, PreTagCommand, ReleaseLevel
from git_release_tag.component import ReleaseInfo
from git_release_tag.logger import log


@click.group(help="release tag support for git repositories")
@click.option("--dry-run", is_flag=True, default=False, help="do not change anything")
@click.option("--verbose", is_flag=True, default=False, help="output")
@click.pass_context
def main(ctx, dry_run, verbose):
    if verbose:
        log.setLevel(logging.DEBUG)
    ctx.obj = ctx.params


@main.command(help="with a release tag")
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
    type=str,
    default="",
    required=False,
    help="to run before version is set and tag is made",
)
@click.argument(
    "directory", type=click.Path(file_okay=False, exists=True), required=True, nargs=-1
)
@click.pass_context
def initialize(ctx, initial_release, tag_prefix, pre_tag_command, directory):

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

@main.command("bump", help="the release")
@click.option("--recursive", "-r", is_flag=True, default=False, help="all directories")
@click.option("--release-level", type=ReleaseLevel(), required=True, help="to bump, either major, minor or patch")
@click.option("--force", is_flag=True, default=False, help="even if there are no changes")
@click.argument(
    "directory", type=click.Path(file_okay=False, exists=True), required=False, nargs=-1
)
@click.pass_context
def bump(ctx, recursive:bool, force:bool, release_level:int, directory):
    components = get_all_release_info(directory, recursive, ctx.obj["dry_run"])

    if not ReleaseInfo.all_tags_unique(components):
        exit(1)

    for component in components:
        component.tag_next_release(release_level, force=force)


@main.command("show", help="current release")
@click.option("--recursive", "-r", is_flag=True, default=False, help="all directories")
@click.option("--with-tags", is_flag=True, default=False, help="of the latest release")
@click.argument(
    "directory", type=click.Path(file_okay=False, exists=True), default=".", required=False, nargs=1
)
@click.pass_context
def show(ctx, recursive, with_tags, directory):

    components = get_all_release_info(directory, recursive, ctx.obj["dry_run"])
    for component in components:
        if recursive:
            if with_tags:
                print(f'{component.directory}\t{component.current_version}\t{component.tag}')
            else:
                print(f'{component.directory}\t{component.current_version}')
        else:
            print(component.current_version)



@main.command("validate", help="integrity of tags")
@click.option("--recursive/--no-recursive", "-r", is_flag=True, default=True, help="all directories")
@click.argument(
    "directory", type=click.Path(file_okay=False, exists=True), required=False, nargs=-1
)
@click.pass_context
def validate(ctx, directory, recursive:bool):
    if not directory:
        directory = ["."]
    components = get_all_release_info(directory, recursive, True)
    if ReleaseInfo.all_tags_unique(components):
        logging.info("ok")


def get_all_release_info(directories: List[str], recursive:bool, dry_run:bool) -> List[ReleaseInfo]:
    result = []
    if not directories:
        directories = ["."]

    if recursive:
        for dir in directories:
            result.extend(
                ReleaseInfo.find_all_subdirectories(dir,dry_run=dry_run)
            )
    else:
        for dir in directories:
            result.append(ReleaseInfo(dir, dry_run=dry_run))

    return sorted(result, key=lambda p: len(os.path.abspath(p.directory).split("/")), reverse=True)



if __name__ == "__main__":
    main()

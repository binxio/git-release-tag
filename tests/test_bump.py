import pytest
import os
import uuid
from git_release_tag.release_info import ReleaseInfo


def test_bump():
    dir = f"/tmp/git-release-tag/bump/{uuid.uuid4()}"
    os.makedirs(dir, exist_ok=True)
    i = ReleaseInfo(path=dir)
    i.git_init()

    ReleaseInfo.initialize(
        directory=dir,
        semver="0.1.0",
        base_tag="",
        pre_tag_command="echo @@RELEASE@@ > release.txt",
        dry_run=False,
    )
    i.read()
    assert i.is_inside_work_tree
    assert i.pre_tag_command == "echo @@RELEASE@@ > release.txt"
    assert i.base_tag == ""
    assert i.semver == "0.1.0"
    assert i.directory == dir
    assert i.path == os.path.join(dir, ".release")

    i.tag_next_release(ReleaseInfo.PATCH, force=False)
    i.read()
    assert i.semver == "0.1.0"
    with open(os.path.join(i.directory, "release.txt")) as f:
        release_txt = f.read()

    assert release_txt.rstrip() == i.semver


def test_bump_force():
    dir = f"/tmp/git-release-tag/bump/{uuid.uuid4()}"
    os.makedirs(dir, exist_ok=True)
    i = ReleaseInfo(path=dir)
    i.git_init()

    ReleaseInfo.initialize(
        directory=dir,
        semver="0.1.0",
        base_tag="",
        pre_tag_command="echo @@RELEASE@@ > release.txt",
        dry_run=False,
    )
    i.read()
    assert i.is_inside_work_tree
    assert i.pre_tag_command == "echo @@RELEASE@@ > release.txt"
    assert i.base_tag == ""
    assert i.semver == "0.1.0"
    assert i.directory == dir
    assert i.path == os.path.join(dir, ".release")

    i.tag_next_release(ReleaseInfo.PATCH, force=True)
    i.read()
    assert i.semver == "0.1.1"
    with open(os.path.join(i.directory, "release.txt")) as f:
        release_txt = f.read()

    assert release_txt.rstrip() == i.semver

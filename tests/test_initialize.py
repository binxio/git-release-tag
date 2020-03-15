import pytest
import os
import uuid
from git_release_tag.release_info import ReleaseInfo


def test_initialize_outside_a_workspace():
    topdir = f"/tmp/git-release-tag/init/{uuid.uuid4()}"
    directories = [os.path.join(topdir, "a"), os.path.join(topdir, "b"), topdir]
    ctx = {"obj": {"dry_run": True, "verbose": True}}
    for dir in directories:
        os.makedirs(dir, exist_ok=True)
    for i, dir in enumerate(directories):
        ReleaseInfo.initialize(
            directory=dir,
            semver=f"0.{i}.0",
            base_tag=(os.path.basename(dir) + "-"),
            pre_tag_command="echo @@RELEASE@@ > release.txt",
            dry_run=False,
        )
        info = ReleaseInfo(path=dir)
        assert info.pre_tag_command == "echo @@RELEASE@@ > release.txt"
        assert info.base_tag == os.path.basename(dir) + "-"
        assert info.semver == f"0.{i}.0"
        assert info.directory == dir
        assert info.path == os.path.join(dir, ".release")
        assert not info.is_inside_work_tree


def test_initialize_in_workspace():
    topdir = f"/tmp/git-release-tag/init/{uuid.uuid4()}"
    directories = [os.path.join(topdir, "a"), os.path.join(topdir, "b"), topdir]
    ctx = {"obj": {"dry_run": True, "verbose": True}}
    for dir in directories:
        os.makedirs(dir, exist_ok=True)
    info = ReleaseInfo(path=topdir)
    info.git_init()
    for i, dir in enumerate(directories):
        ReleaseInfo.initialize(
            directory=dir,
            semver=f"0.{i}.0",
            base_tag=(os.path.basename(dir) + "-"),
            pre_tag_command="echo @@RELEASE@@ > release.txt",
            dry_run=False,
        )
        info = ReleaseInfo(path=dir)
        assert info.is_inside_work_tree
        assert info.pre_tag_command == "echo @@RELEASE@@ > release.txt"
        assert info.base_tag == os.path.basename(dir) + "-"
        assert info.semver == f"0.{i}.0"
        assert info.directory == dir
        assert info.path == os.path.join(dir, ".release")

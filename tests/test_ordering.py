import pytest
import os
import uuid
from git_release_tag.release_info import ReleaseInfo


def test_ordering():
    dir = f"/tmp/git-release-tag/ordered/{uuid.uuid4()}"
    subdirs = [f"{dir}/a", f"{dir}/b", f"{dir}/c", f"{dir}/c/d", f"{dir}/e"]
    depends = {
        f"{dir}/e": ["../c"],
        f"{dir}/b": ["../a"],
        f"{dir}/c": ["../b"],
        f"{dir}/c/d": ["../../a"],
    }

    os.makedirs(dir, exist_ok=True)
    i = ReleaseInfo(path=dir)
    i.git_init()

    for d in subdirs:
        os.makedirs(d, exist_ok=True)

        ReleaseInfo.initialize(
            directory=d,
            semver="0.1.0",
            base_tag=f"{os.path.basename(d)}-",
            pre_tag_command="echo @@RELEASE@@ > release.txt",
            tag_on_changes_in=depends.get(d, ["."]),
            dry_run=False,
        )

    infos = ReleaseInfo.find_all([dir], True, True)

    expect = [f"{dir}/a", f"{dir}/c/d", f"{dir}/b", f"{dir}/c", f"{dir}/e"]
    assert expect == list(map(lambda i: i.directory, infos))
    print(infos)


def test_cycle():
    dir = f"/tmp/git-release-tag/ordered/{uuid.uuid4()}"
    subdirs = [f"{dir}/a", f"{dir}/b", f"{dir}/c"]
    depends = {
        f"{dir}/a": ["../b"],
        f"{dir}/b": ["../c"],
        f"{dir}/c": ["../a"],
    }

    os.makedirs(dir, exist_ok=True)
    i = ReleaseInfo(path=dir)
    i.git_init()

    for d in subdirs:
        os.makedirs(d, exist_ok=True)

    for d in subdirs:
        ReleaseInfo.initialize(
            directory=d,
            semver="0.1.0",
            base_tag=f"{os.path.basename(d)}-",
            pre_tag_command="echo @@RELEASE@@ > release.txt",
            tag_on_changes_in=depends.get(d, ["."]),
            dry_run=False,
        )

    try:
        infos = ReleaseInfo.find_all([dir], True, True)
    except ValueError as error:
        assert error.args and error.args[0].startswith("cycle detected")

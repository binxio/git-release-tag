import os, re, logging
from typing import List, Any
import subprocess
import fnmatch
from typing import List, Optional
from git_release_tag.logger import log
from git_release_tag import git


class ReleaseInfo(object):
    PATCH = 2
    MINOR = 1
    MAJOR = 0

    def __init__(self, path: str, dry_run: bool = False):
        super(ReleaseInfo, self).__init__()
        self.dry_run = dry_run
        self.directory = path
        self.path = os.path.join(self.directory, ".release")

        self.base_tag = None
        self._semver = None
        self._pre_tag_command = None

        if not os.path.isdir(self.directory):
            log.error(f"directory {self.directory} does not exist")
            exit(1)

        if self.has_release_configuration:
            self.read()

    @property
    def has_release_configuration(self) -> bool:
        return os.path.exists(self.path)

    @property
    def semver(self):
        return self._semver

    @semver.setter
    def semver(self, value):
        if value and not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", value):
            raise ValueError(
                f"semantic version of release '{self.semver}' does not match release <major>.<minor>.<patch>"
            )
        self._semver = value

    @property
    def pre_tag_command(self):
        return self._pre_tag_command

    @pre_tag_command.setter
    def pre_tag_command(self, value):
        if value:
            allowed = set(["RELEASE", "TAG", "BASE_TAG"])
            refs = set(re.findall(r"@@([a-zA-Z_]+)@@", value))
            unsupported = refs.difference(allowed)
            if unsupported:
                raise ValueError(f"found unsupported references {unsupported}")
            if "RELEASE" not in refs:
                raise ValueError(
                    f"expected at least a @@RELEASE@@ reference in pre tag command: '{value}' of {self.directory}"
                )

        self._pre_tag_command = value

    @property
    def tag(self):
        return f"{self.base_tag}{self.semver}"

    @property
    def all_tags(self) -> List[str]:
        return list(
            map(lambda l: l.strip(), self.git_query(["git", "tag"]).split("\n"))
        )

    def read(self):
        result = {}
        with open(self.path, "r") as f:
            for line in f:
                line = line.rstrip()
                if len(line) > 0 and line[0] != "#":
                    value = line.split("=", 1)
                    result[value[0].strip()] = value[1].strip()
        if not ("release" in result and "tag" in result):
            log.error(f"{self.path} does not contain release and/or tag values")
            exit(1)

        if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", result["release"]):
            log.error(
                f"ERROR: incorrect format of release in {self.path}, expected <major.minor.patch>"
            )
            exit(1)

        match = re.fullmatch(
            r"(?P<base_tag>.*)(?P<release>[0-9]+\.[0-9]+\.[0-9]+$)", result["tag"]
        )
        if not match:
            log.error(
                f"ERROR: incorrect format old the tag in {self.path}, expected tag <base><major.minor.patch>"
            )
            exit(1)

        self.semver = result["release"]
        self.pre_tag_command = result.get("pre_tag_command")
        self.base_tag = match.group("base_tag")
        if match.group("release") != self.semver:
            log.warning(
                f"tag {self.tag} in {self.path} does not match specified release {match.group('release')}"
            )

    def __repr__(self):
        return self.path

    def write(self):
        log.debug(f"writing {self.path}")
        if self.dry_run:
            return

        with open(self.path, "w") as f:
            f.write("release=%s\n" % self.semver)
            f.write("tag=%s\n" % self.tag)
            if self.pre_tag_command:
                f.write("pre_tag_command=%s\n" % self.pre_tag_command)

    def next_version(self, level):
        assert self.semver
        release = list(map(lambda n: int(n), self.semver.split(".")))
        if level == ReleaseInfo.PATCH:
            release[ReleaseInfo.PATCH] += 1
        elif level == ReleaseInfo.MINOR:
            release[ReleaseInfo.MINOR] += 1
            release[ReleaseInfo.PATCH] = 0
        elif level == ReleaseInfo.MAJOR:
            release[ReleaseInfo.MAJOR] += 1
            release[ReleaseInfo.MINOR] = 0
            release[ReleaseInfo.PATCH] = 0
        else:
            log.error("I can only bump PATCH, MINOR or MAJOR levels")
            exit(1)

        self.semver = "%d.%d.%d" % (release[0], release[1], release[2])

    def git_query(self, cmd: List[str], fail_on_error: bool = True) -> str:
        out, process = git.exec(
            cmd, self.directory, dry_run=False, fail_on_error=fail_on_error
        )
        return out[0]

    def git_update(self, cmd: List[str]) -> str:
        out, process = git.exec(
            cmd, self.directory, dry_run=self.dry_run, fail_on_error=True
        )
        return out[0]

    @property
    def is_inside_work_tree(self):
        cmd = ["git", "rev-parse", "--is-inside-work-tree"]
        out, process = git.exec(cmd, self.directory, dry_run=False, fail_on_error=False)
        return process.returncode == 0 and out[0].strip() == "true"

    @property
    def git_prefix(self):
        return (
            self.git_query(["git", "rev-parse", "--show-prefix"]).rstrip().rstrip("/")
        )

    @property
    def short_revision(self) -> str:
        return self.git_query(["git", "log", "-n", "1", "--format=%h", "."]).rstrip()

    @property
    def changes_since_tag(self) -> str:
        return self.git_query(
            ["git", "diff", "--shortstat", "-r", self.tag, "--", "."]
        ).rstrip()

    @property
    def change_list(self) -> List[str]:
        return list(
            filter(
                lambda c: c, self.git_query(["git", "status", "-s", "."]).split("\n")
            )
        )

    @property
    def current_version(self):
        if self.change_list:
            return f"{self.semver}-{self.short_revision}-dirty"
        elif self.changes_since_tag:
            return f"{self.semver}-{self.short_revision}"
        else:
            return self.semver

    def tag_next_release(self, level, message: str = None, force: bool = False):
        if not force:
            if not self.changes_since_tag:
                log.info(f"{self.directory} has no changes since {self.semver}.")
                return

        self.next_version(level)
        if self.tag in self.all_tags:
            log.error(f"tag {self.tag} already exists")
            exit(1)

        self.write()
        if not message:
            message = f"bumped {self.git_prefix} to release {self.semver}"
        self.commit_and_tag(message)

    def git_init(self):
        self.git_update(["git", "init"])

    def commit_and_tag(self, message: str):
        self.exec_pre_tag_command()

        changes = list(map(lambda s: s[3:], self.change_list))
        if changes:
            log.info(f"commit changes to {', '.join(changes)} in {self.directory}")
            self.git_update(["git", "add", "."])
            self.git_update(["git", "commit", "-m", message])
        else:
            log.info(f"no changes to commit in {self.directory}")


        self.git_update(["git", "tag", self.tag])
        log.info(f"release {self.semver} of {self.directory} tagged by {self.tag}")

    @staticmethod
    def initialize(
        directory: str,
        semver: str = "0.0.0",
        base_tag: str = "",
        pre_tag_command: str = "",
        dry_run: bool = False,
    ) -> bool:

        if not os.path.isdir(directory):
            log.error(f"{directory} is not a directory.")
            exit(1)

        path = os.path.join(directory, ".release")
        if os.path.exists(path):
            log.error(f"{directory} is ready initialized.")
            return False

        info = ReleaseInfo(path=directory, dry_run=dry_run)
        info.semver = semver
        info.base_tag = base_tag
        info.pre_tag_command = pre_tag_command

        if info.is_inside_work_tree and info.tag in info.all_tags:
            log.error(f'tag {info.tag} already exist in git repository for {info.path}')
            exit(1)

        info.write()
        if info.is_inside_work_tree:
            info.commit_and_tag(
                f"initialized {info.git_prefix} to release {info.semver}"
            )
        else:
            log.warning(f"{info.path} is not inside a git workspace")

        return True

    def process_pre_tag_command(self):
        result = self.pre_tag_command.replace("@@RELEASE@@", self.semver)
        result = result.replace("@@TAG@@", self.tag)
        return result.replace("@@BASE_TAG@@", self.base_tag)

    def exec_pre_tag_command(self):
        if self.dry_run and self.pre_tag_command:
            log.debug(f"$ {self.pre_tag_command}")
            return

        if self.pre_tag_command:
            cmd = self.process_pre_tag_command()
            process = subprocess.Popen(
                cmd,
                shell=True,
                cwd=self.directory,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            out = process.communicate()
            if process.returncode != 0:
                log.error(
                    f"{self.pre_tag_command} in {self.directory}, returned {process.returncode}, output {out[1]}"
                )
                exit(1)
            return out[0]

    @staticmethod
    def validate(release_infos: List["ReleaseInfo"]) -> bool:
        result = True
        base_tags = {}
        for release_info in release_infos:

            base_tag = release_info.base_tag
            existing = base_tags.get(base_tag)
            if release_info.base_tag in base_tags:
                log.error(
                    f"{release_info.path} has the same base tag as {existing.path}: {base_tag}"
                )
                result = False
            else:
                base_tags[base_tag] = release_info

            if not release_info.is_inside_work_tree:
                log.error(f"{release_info.directory} is not inside a git workspace")
                result = False
            else:
                if release_info.tag not in release_info.all_tags:
                    log.error(
                        f"tag {release_info.tag} in {release_info.path} does not exist in repository"
                    )
                    result = False

        return result

    #staticmethod
    def find_all(directories: Optional[List[str]], recursive:bool, dry_run:bool) -> List["ReleaseInfo"]:
        """
        filters all directories with a .release configuration and returns a list of ReleaseInfo.
        if recursive is specified the directories are traversed to find all subdirectories with a .release.
        If no directories are specified, the current working directory is used.
        The resulting list is sorted depth first, to ensure that parent directories are processed last.
        """
        result = []
        if not directories:
            directories = ["."]

        if recursive:
            for dir in directories:
                for root, _, files in os.walk(dir, topdown=False):
                    for item in fnmatch.filter(files, ".release"):
                        info = ReleaseInfo(path=os.path.join(root), dry_run=dry_run)
                        info.read()
                        result.append(info)
        else:
            for dir in directories:
                result.append(ReleaseInfo(dir, dry_run=dry_run))

        return sorted(result, key=lambda p: len(os.path.abspath(p.directory).split("/")), reverse=True)

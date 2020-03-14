from typing import List
from git_release_tag.logger import log
import subprocess


def exec(cmd: List[str], cwd: str, dry_run:bool=False, fail_on_error: bool = True):
    log.debug("$ %s  #cwd = %s", " ".join(cmd), cwd)

    if dry_run:
        return ("", ""), None

    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    out = process.communicate()
    log.debug("returncode = %s", process.returncode)
    log.debug("stdout = %s", out[0])
    log.debug("stderr = %s", out[1])
    if fail_on_error and process.returncode != 0:
        log.error("%s failed, %s", " ".join(cmd), out[1])
        exit(1)

    return out, process

from typing import List
import re
from git_release_tag.logger import log
import subprocess


def _to_cli(cmd:List[str]):
    return " ".join(map(lambda s: f"'{s}'" if re.findall(r"\s", s) else s, cmd))

def exec(cmd: List[str], cwd: str, dry_run:bool=False, fail_on_error: bool = True):
    log.debug("$ %s  #cwd = %s", _to_cli(cmd), cwd)

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
        log.error("%s failed in %s, %s", " ".join(cmd), cwd, (out[0]+out[1]))
        exit(1)

    return out, process

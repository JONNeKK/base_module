import os
import shutil
from subprocess import check_output, SubprocessError
from typing import Tuple

import logging
log = logging.getLogger(__name__)


def get_git_commit_hash() -> Tuple[str, str]:
    git_hash = "unknown"
    git_repo_name = "not a git repository"

    git_bin = shutil.which("git") # Vulnerable to Path hijacking...
    if not git_bin:
        return git_hash, git_repo_name

    try:
        git_root = check_output(
            [git_bin, "rev-parse", "--show-toplevel"],
            timeout=1,
            env={"PATH": os.environ.get("PATH", "")},
        ).strip().decode()

        git_hash = check_output(
            [git_bin, "rev-parse", "HEAD"],
            cwd=git_root,
            timeout=1,
            env={"PATH": os.environ.get("PATH", "")},
        ).strip().decode()

        git_repo_name = check_output(
            [git_bin, "config", "--get", "remote.origin.url"],
            cwd=git_root,
            timeout=1,
            env={"PATH": os.environ.get("PATH", "")},
        ).strip().decode()

    except SubprocessError as e:
        log.warning(e)

    return git_hash, git_repo_name

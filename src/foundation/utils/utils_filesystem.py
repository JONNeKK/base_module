import logging
import argparse
from dataclasses import is_dataclass
from typing import get_origin, get_args

from pathlib import Path

log = logging.getLogger(__name__)


# working with filesystem
def ensure_dir_exists(path:Path) -> Path:
    if not Path.exists(path):
        Path.mkdir(path, parents=True, exist_ok=True)
    return path


def maybe_ensure_dir_exists(path: Path, mkdir: bool) -> Path:
    if mkdir:
        return ensure_dir_exists(path)
    else:
        return path


def safe_ensure_dir_exists(path: Path) -> Path:
    """Should be safer in multi-treaded environment."""
    try:
        return ensure_dir_exists(path)
    except FileExistsError:
        return path


def remove_if_exists(file: Path):
    try:
        file.unlink()
        log.debug("File %s deleted successfully." % str(file))
    except FileNotFoundError:
        log.error("The file %s does not exist." % str(file))
    except IsADirectoryError:
        log.error("The path %s is a directory, not a file." % str(file))
    except PermissionError:
        log.error("You don't have permission to delete this file %s." % str(file))




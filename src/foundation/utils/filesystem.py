import os
import tempfile
from typing import Callable, TextIO, BinaryIO
from pathlib import Path

import logging
log = logging.getLogger(__name__)


# working with filesystem
def ensure_dir_exists(path:Path) -> Path:
    if not Path.exists(path):
        Path.mkdir(path, parents=True, exist_ok=True)
    return path


def ensure_parents_exist(path:Path) -> Path:
    if not Path.exists(path.parent):
        Path.mkdir(path.parent, parents=True, exist_ok=True)
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



def atomic_write(
        path: str | Path, 
        writer: Callable[[TextIO | BinaryIO], None], 
        *, 
        encoding: str | None ="utf-8"):
    """Atomically write text or binary data to a file.
    Use writer to define how data is written to fiel.

    Args:
        path: Destination file path.
        writer: Callable that writes content to the file.
        encoding: Text encoding, or None for binary mode.

    Returns:
        None.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(dir=path.parent) # Make .tmp file

    try:
        # Open .tmp file by its file descriptor (kernel side int ot identify the file)
        if encoding is None:
            f = os.fdopen(fd, "wb")
        else:
            f = os.fdopen(fd, "w", encoding=encoding)
        # Write the file. 
        with f:
            writer(f)
            f.flush() # Sync all changes from python to the os
            os.fsync(f.fileno()) # Sync all changes from os cache to persistent storage

        os.replace(tmp_path, path) # Atomic write
        # sync directory metadata to persistent memory
        dir_fd = os.open(path.parent, os.O_DIRECTORY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    # delete .tmp file if any Exception happens (this includes Keyboard Interrupt & SystemExit)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        raise



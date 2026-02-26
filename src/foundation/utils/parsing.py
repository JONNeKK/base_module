import logging
import argparse
from dataclasses import is_dataclass
from typing import get_origin, get_args

from pathlib import Path

log = logging.getLogger(__name__)



# CLI parsing
def str2bool(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, str) and v.lower() in ("true",):
        return True
    elif isinstance(v, str) and v.lower() in ("false",):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected")


def is_dataclass_type(tp):
    if is_dataclass(tp):
        return True

    origin = get_origin(tp)
    if origin is None:
        return False

    return any(is_dataclass(arg) for arg in get_args(tp))



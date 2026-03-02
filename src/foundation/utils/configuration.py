from typing import Dict, Any, Type, List
import json
from datetime import date, datetime
from pathlib import Path
from decimal import Decimal
from uuid import UUID
from enum import Enum

import logging
log = logging.getLogger(__name__)


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        if isinstance(o, Decimal):
            return str(o)
        if isinstance(o, UUID):
            return str(o)
        if isinstance(o, Enum):
            return o.value
        if isinstance(o, (set, frozenset)):
            return list(o)
        if isinstance(o, Path):
            return str(o)
        if isinstance(o, Type):
            return str(o)

        return super().default(o)

# --- central default converters ---
DEFAULT_CONVERTERS: Dict[Type, Any] = {
    datetime: datetime.fromisoformat,
    date: date.fromisoformat,
    Decimal: Decimal,
    UUID: UUID,
    Path: Path,
}

DEFAULT_CAST: List[Type] = [list, tuple, set]


def deep_merge(original: Dict, new: Dict) -> Dict:
    """
    Recursively merge `new` into `original`.
    Values in `new` overwrite those in `original`.
    """
    for key, value in new.items():
        if (
            key in original
            and isinstance(original[key], dict)
            and isinstance(value, dict)
        ):
            deep_merge(original[key], value)
        else:
            if key not in original.keys():
                log.info(f"DEEPMERGE: Adding key {key} with value {value}")
                original[key] = value
            elif value != original[key]:
                log.info(f"DEEPMERGE: Overwriting key {key} with value {value}")
                original[key] = value
            else:
                log.debug(f"DEEPMERGE: {value} for {key} already exists.")
    return original


def apply_overwrite(config_dict: dict, key: str, value: Any):
    """
    Apply a nested dataclass overwrite into a nested dictionary.
    Creates missing intermediate dictionaries automatically.
    Performs deep merge if both existing and new values are dicts.
    """
    keys = key.split(".")
    d = config_dict

    # Traverse nested dataclasses and create intermediate dictionaries, if not existant in config_dict
    for k in keys[:-1]:
        if k not in d:
            log.warning("Intermediate key %s not in original dictionary!" % (k))
            d[k] = {}
        elif not isinstance(d[k], dict):
            raise TypeError(f"Cannot descend into non-dict key: '{k}'")
        d = d[k]

    final_key = keys[-1]

    # If both existing and new values are dicts use deep merge, else just overwrite.
    if (
        final_key in d
        and isinstance(d[final_key], dict)
        and isinstance(value, dict)
    ):
        deep_merge(d[final_key], value)
    else: # Handle wrong types while initializing config?
        if final_key not in d.keys():
                log.info(f"DEEPMERGE: Adding key {key} with value {value}")
                d[final_key] = value
        elif value != d[final_key]:
            log.info(f"Overwriting key {key} with value {value}")
            d[final_key] = value
        else:
            log.debug(f"Value {value} for key {key} already exists.")



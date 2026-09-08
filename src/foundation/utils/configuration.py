from typing import Any, Type, List
import json
from copy import deepcopy
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


DEFAULT_CAST: List[Type] = [list, tuple, set]


def deep_merge(
    original: dict[str, Any],
    new: dict[str, Any],
    *,
    modify_in_place: bool = False,
    allow_new_keys: bool = True,
) -> dict[str, Any]:
    """
    Recursively merge `new` into `original`.

    Existing values are overwritten by values from `new`.
    Nested dictionaries are merged recursively.

    Args:
        original: Dictionary to use as the base for the merge.
        new: Dictionary whose values are merged into `original`.
        modify_in_place: If True, modify `original` directly.
            If False, merge into a deep copy of `original`.
        allow_new_keys: If False, keys not already present in
            `original` are ignored.

    Returns:
        The merged dictionary. If `modify_in_place` is True,
        this is the same object as `original`.

    """
    if modify_in_place:
        result = original
    else:
        result = deepcopy(original)

    for key, value in new.items():
        if key not in result:
            if allow_new_keys:
                result[key] = deepcopy(value)
            continue

        if isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(
                result[key],
                value,
                modify_in_place=modify_in_place,
                allow_new_keys=allow_new_keys,
            )
        else:
            result[key] = deepcopy(value)

    return result



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



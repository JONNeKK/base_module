from typing import Dict, Any, Type, List
import json
from datetime import date, datetime
from pathlib import Path
from decimal import Decimal
from uuid import UUID
from enum import Enum


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


def apply_overwrite(config_dict: dict, key: str, value: Any):
    keys = key.split(".")
    d = config_dict
    for k in keys[:-1]:
        d = d[k]
    d[keys[-1]] = value


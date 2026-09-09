from dataclasses import dataclass, asdict, field, fields, is_dataclass
from typing import (
    Optional, 
    Dict, 
    Any, 
    Type, 
    TypeVar, 
    ClassVar, 
    Callable, 
    Generic,
    get_args, 
    get_origin, 
    get_type_hints,
    cast
) 
import logging
import json
from datetime import datetime, date
from pathlib import Path
from decimal import Decimal
from enum import Enum
from uuid import UUID
from dacite import from_dict as dacite_from_dict, Config as DaciteConfig

from .utils.parsing import is_dataclass_type
from .utils.filesystem import ensure_dir_exists, ensure_parents_exist
from .utils.configuration import CustomJSONEncoder, DEFAULT_CAST, apply_overwrite
from .utils.git import get_git_commit_hash

log = logging.getLogger(__name__)

TConfig = TypeVar("TConfig", bound="BaseConfig")


@dataclass
class BaseConfig:
    """
    Config Class storing all relevant parameters. Some can be overwritten 
    by command line arguments. All that are set to None should be overwritten.
    This is not enforced, so beware of runtime errors.
    """
    CONFIG_VERSION: ClassVar[int]

    # File Context
    cfg_save_dir: Path      = Path("configs")
    current_run_dir: Path   = Path.cwd()

    # Git
    git_hash: str       = "empty"
    git_repo_name: str  = "empty"

    # Config
    cfg_file_name_save: Optional[str]               = None
    cfg_file_name_load: Optional[str]               = None
    overwrite_from_cmd: bool                         = False
    json_encoder: ClassVar[Type[json.JSONEncoder]]  = CustomJSONEncoder

    cmd_args: Dict[str, Any]    = field(default_factory=dict)

    # Debug Flags
    debug: bool = False

    # Logging
    log_dir: Optional[str]  = None
    log_level: int          = logging.INFO


    # Extras which can be arbitrarily defined at runtime
    extras: Dict[str, Any]  = field(default_factory=dict)



    def __post_init__(self):
        if self.debug:
            log.info("Debugging enabled!")
            self.log_level = logging.DEBUG
            log.debug("Retrieving git hash & repo name")
            self.git_hash, self.git_repo_name = get_git_commit_hash()

    
    @classmethod
    def collect_nested_dataclasses(cls):
        return [f.name for f in fields(cls) if is_dataclass_type(f.type)]



    def get_cfg_file_path(self, mode: str) -> Path:
        if mode == "load":
            cfg_file_name = self.cfg_file_name_load
        elif mode == "save":
            cfg_file_name = self.cfg_file_name_save
        else:
            raise NameError(f"Incorrect mode {mode} specified in Config.get_cfg_file_path!")
        assert cfg_file_name, "There is no file name to return a config"
        json_name = cfg_file_name + '.json'
        return ensure_dir_exists(self.current_run_dir / self.cfg_save_dir) / json_name
    
    def get_logfile_path(self) -> Path:
        assert self.log_dir, "No log directory specified!"
        logfile_name = f"log_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
        return ensure_dir_exists(self.current_run_dir / self.log_dir) / logfile_name

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_str(self) -> str:
        cfg_lines = []
        for field in fields(self):
            cfg_lines.append(f"{field.name}={getattr(self, field.name)}")
        return "\n".join(cfg_lines)

    @classmethod 
    def extra_type_hooks(cls) -> dict[type, Callable[[Any], Any]]: 
        return { 
            Path: Path, 
            UUID: UUID, 
            Decimal: Decimal,
            datetime: datetime.fromisoformat, 
            date: date.fromisoformat,
        }

    @classmethod
    def build_type_hooks(cls) -> dict[type, Callable[[Any], Any]]:
        """Build dacite type hooks for enums found in a dataclass tree."""

        hooks: dict[type, Callable[[Any], Any]] = {}
        visited: set[type] = set()

        def visit_annotation(annotation: Any) -> None:
            origin = get_origin(annotation)

            if origin is None:
                if not isinstance(annotation, type):
                    return

                if issubclass(annotation, Enum):
                    hooks.setdefault(
                        annotation,
                        lambda value, enum_cls=annotation: enum_cls(value),
                    )
                    return

                if is_dataclass(annotation):
                    visit_dataclass(annotation)

                return

            for arg in get_args(annotation):
                visit_annotation(arg)

        def visit_dataclass(dataclass_type: type) -> None:
            if dataclass_type in visited:
                return

            visited.add(dataclass_type)
            
            extra_type_hooks = getattr(dataclass_type, "extra_type_hooks", None)
            if callable(extra_type_hooks):
                extra_type_hooks = cast(
                    Callable[[], dict[type, Callable[[Any], Any]]],
                    extra_type_hooks,
                )
                hooks.update(extra_type_hooks())


            type_hints = get_type_hints(dataclass_type)

            for field in fields(dataclass_type):
                visit_annotation(type_hints[field.name])

        visit_dataclass(cls)

        return hooks

    @classmethod
    def from_dict(cls, data: dict):
        hooks = cls.build_type_hooks()

        return dacite_from_dict(
            data_class=cls,
            data=data,
            config=DaciteConfig(type_hooks=hooks, cast=DEFAULT_CAST)
        )


    def validate(self):
        pass


class BaseConfigManager(Generic[TConfig]):
    """Load and save a specific BaseConfig type."""

    def __init__(self, config_type: type[TConfig]):
        self.config_type = config_type

    def save(self, config: TConfig, path: Path) -> None:
        """Save a configuration to JSON."""
        path.parent.mkdir(parents=True, exist_ok=True)

        log.info("Saving configuration to %s", path)

        data = config.to_dict()

        # CONFIG_VERSION is class metadata, so it is not included
        # by dataclasses.asdict().
        data["config_version"] = config.CONFIG_VERSION

        with path.open("w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                indent=2,
                cls=config.json_encoder,
            )

    def load(self, path: Path) -> TConfig:
        """Load a configuration from JSON."""
        if not path.is_file():
            raise FileNotFoundError(
                f"Configuration file not found: {path}"
            )

        log.info("Loading configuration from %s", path)

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        stored_version = data.get("config_version")

        if stored_version is None:
            raise ValueError(
                f"Configuration {path} has no config_version"
            )

        if stored_version != self.config_type.CONFIG_VERSION:
            raise ValueError(
                f"Configuration version mismatch for {self.config_type.__name__}: "
                f"file={stored_version}, "
                f"current={self.config_type.CONFIG_VERSION}"
            )

        # config_version is metadata rather than a dataclass field.
        data.pop("config_version", None)

        config = self.config_type.from_dict(data)
        config.validate()

        return config

    
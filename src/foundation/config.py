from dataclasses import dataclass, asdict, field, fields
from typing import Optional, Dict, Any, Type, TypeVar, ClassVar
import logging
import json
from datetime import datetime
from pathlib import Path
from enum import Enum
from dacite import from_dict as from_dict_dacite, Config

from .utils.utils_parsing import is_dataclass_type
from .utils.utils_filesystem import ensure_dir_exists, ensure_parents_exist
from .utils.utils_config import CustomJSONEncoder, DEFAULT_CAST, DEFAULT_CONVERTERS

log = logging.getLogger(__name__)

TConfig = TypeVar("TConfig", bound="BaseConfig")


@dataclass
class BaseConfig:
    """
    Config Class storing all relevant parameters. Some can be overwritten 
    by command line arguments. All that are set to None should be overwritten.
    This is not enforced, so beware of runtime errors.
    """

    # File Context
    cfg_save_dir: Path              = Path("configs")
    current_run_dir: Path           = Path.cwd()

    # Config
    cfg_file_name_save: Optional[str]               = None
    cfg_file_name_load: Optional[str]               = None
    override_from_cmd: bool                         = False
    json_encoder: ClassVar[Type[json.JSONEncoder]]  = CustomJSONEncoder

    cmd_args: Dict[str, Any]            = field(default_factory=dict)

    # Debug Flags
    debug: bool                     = False

    # Logging
    log_dir: Optional[str]      = None
    log_level: int              = logging.DEBUG


    # Extras which can be arbitrarily defined at runtime
    extras: Dict[str, Any]      = field(default_factory=dict)



    def __post_init__(self):
        pass

    
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

    def update_from_dict(self, dict_data: Dict, dict_key: str = "extras") -> None:
        extras_dict_tmp = getattr(self, dict_key)
        # Loop through the extra attributes
        for key, value in dict_data[dict_key].items():
            if hasattr(extras_dict_tmp, key):
                if getattr(extras_dict_tmp,key) != value:
                    log.debug("Overriding %s arg %r with value %r passed from command line", dict_key, key, value)
                    extras_dict_tmp[key] = value
            else:
                log.debug("Adding new %s arg %r with value %r that is not in the saved config file", dict_key, key, value)
                extras_dict_tmp[key] = value
        setattr(self, dict_key, extras_dict_tmp)

    def update(self, data: Dict) -> None:
        for key, value in data.items():
            if hasattr(self, key):
                if getattr(self,key) != value:
                    # Deal with extras
                    if key == "extras":
                        self.update_from_dict(data[key], key)
                    else:
                        log.debug("Overriding arg %r with value %r passed from command line", key, value)
                        setattr(self, key, value)
            else:
                log.warning("Command Line arg %r with value %r does not match Config Key", key, value)
        log.info("Fully updated the Config Class!")


    def save(self, cfg_save_filename: Optional[Path] = None) -> None:
        if cfg_save_filename == None:
            cfg_save_filename = self.get_cfg_file_path("save")
        else:
            ensure_parents_exist(cfg_save_filename)
        assert cfg_save_filename is not None, "cfg_save_dir must be set before saving config"
        with open(cfg_save_filename, "w") as f:
            json.dump(self.to_dict(), f, indent=2, cls=self.json_encoder) # Alternative would be to adjust self.to_dict()

    @classmethod
    def build_type_hooks(cls) -> Dict[Type, Any]:
        hooks = dict(DEFAULT_CONVERTERS)  # start with base converters

        # automatically add Enum converters for any Enum fields
        for f in fields(cls):
            if isinstance(f.type, type) and issubclass(f.type, Enum):
                hooks[f.type] = lambda v, t=f.type: t(v)
        return hooks

    @classmethod
    def from_dict(cls, data: dict):
        hooks = {}
        for base in reversed(cls.__mro__):
            if hasattr(base, "build_type_hooks"):
                hooks.update(base.build_type_hooks())

        return from_dict_dacite(
            data_class=cls,
            data=data,
            config=Config(type_hooks=hooks, cast=DEFAULT_CAST)
        )

    @classmethod
    def cfg_load(cls: Type[TConfig], cfg_filename: Path) -> TConfig:

        if not Path.is_file(cfg_filename):
            raise Exception(
                f"Could not load saved parameters for experiment {cls.cfg_file_name_load} "
                f"(file {cfg_filename} not found). Check that you have the correct experiment name "
                f"and --train_dir is set correctly."
            )

        with open(cfg_filename, "r") as json_file:
            json_params = json.load(json_file)
            log.warning("Loading existing experiment configuration from %s", cfg_filename)
            log.debug(json_params)

        loaded_cfg: "BaseConfig" = cls.from_dict(json_params)

        if loaded_cfg.override_from_cmd:
            log.debug("Start overriding from cmd")
            loaded_cfg.update(cls.cmd_args)
        
        return loaded_cfg

    def validate(self):
        pass



    
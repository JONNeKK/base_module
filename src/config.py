from dataclasses import dataclass, asdict, field, fields
from typing import Optional, Tuple, Dict, Any, TypeVar, Type
import logging
import json
import datetime
from pathlib import Path

from src.utils import is_dataclass_type, ensure_dir_exists


log = logging.getLogger(__name__)


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
    cfg_file_name_save: Optional[str]   = None
    cfg_file_name_load: Optional[str]   = None
    override_from_cmd: bool             = False
    cmd_args: Dict[str, Any]            = field(default_factory=dict)

    # Debug Flags
    debug: bool                     = False

    # Logging
    log_dir: Optional[str]      = None
    log_level: int              = logging.DEBUG


    # Extras which can be arbitrarily defined at runtime
    extras: Dict[str, Any]      = field(default_factory=dict)



    def __post_init__(self):
        nested_classes = self.collect_nested_dataclasses()
        for nested_class in nested_classes:
            dict_item = getattr(self, nested_class)
            type_item = self.__annotations__.get(nested_class)
            assert type_item
            assert isinstance(dict_item, dict)
            setattr(self, nested_class, type_item(**dict_item))
        # If I want to avoid using dacite, I need to redeclare the nested dataclasses here! 
        # Would be nice to actually do this at some point to avoid extra dependencies.
        # However the current setup allows for more than two nested layers. Don't know yet if that is really necessary
    
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
        return ensure_dir_exists(self.current_run_dir / self.cfg_save_dir / json_name)
    
    def get_logfile_path(self) -> Path:
        assert self.log_dir, "No log directory specified!"
        logfile_name = f"log_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
        return ensure_dir_exists(self.current_run_dir / self.log_dir / logfile_name)

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


    def save(self) -> None:
        assert self.cfg_save_dir is not None, "run_dir must be set before saving config"
        self.cfg_save_dir.mkdir(parents=True, exist_ok=True)
        with open(self.get_cfg_file_path("save"), "w") as f:
            json.dump(self.to_dict(), f, indent=2, cls=PathEncoder) # Alternative would be to adjust self.to_dict()


    @classmethod
    def convert2fields(cls, json_params):
        # Converting Strings back to Paths when necessary
        path_fields = {f.name for f in fields(cls) if f.type == Path}
        for key in path_fields:
            if key in json_params and json_params[key] is not None:
                json_params[key] = Path(json_params[key])
                
        # Converting arrays back to Tuples when necessary
        tuple_fields = {f.name for f in fields(cls) if f.type == Tuple}
        for key in tuple_fields:
            if key in json_params and json_params[key] is not None:
                json_params[key] = tuple(json_params[key])

    @classmethod
    def cfg_load(cls: Type["BaseConfig"], cfg_filename: Path) -> "BaseConfig":

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
        
        cls.convert2fields(json_params)

        
        loaded_cfg: "BaseConfig" = cls(**json_params)

        if loaded_cfg.override_from_cmd:
            log.debug("Start overriding from cmd")
            loaded_cfg.update(cls.cmd_args)
        
        return loaded_cfg

    def postprocess(self):
        pass
        

    def validate(self):
        pass



class PathEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Path):
            return str(o)  # Convert Path to string
        return super().default(o)
    
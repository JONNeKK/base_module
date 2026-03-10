import logging
import argparse
import json
from typing import Dict, Any, Tuple, Type, Callable, List, TypeVar, Generic

from .arguments import add_extra_params, add_config_params
from .config import BaseConfig

log = logging.getLogger(__name__)

ParamFunc = Callable[[argparse.ArgumentParser], None]
TConfig = TypeVar("TConfig", bound="BaseConfig")


class BaseCLIParser(Generic[TConfig]):
    config_class: Type[TConfig]
    _param_funcs: List[ParamFunc]

    def __init__(self, config_class: Type[TConfig]) -> None:
        self.config_class = config_class # Overwrite this if you are using another Config!!
        self._param_funcs = [add_extra_params, add_config_params] # Add other functions to this list!

    def append_param_func(self, param_func: ParamFunc):
        self._param_funcs.append(param_func)

    def build_parser(self, argv) -> Tuple[argparse.ArgumentParser, argparse.Namespace]:
        parser = argparse.ArgumentParser(description="Run experiment")

        for param_func in self._param_funcs:
            param_func(parser)

        args, _ = parser.parse_known_args(argv)
        return parser, args

    def parse_value(self, v: str) -> Any:
        try:
            return json.loads(v)
        except Exception as e:
            log.warning(e)
            return v

    def parse_dict(self, items) -> Dict[str, Any]:
        d = {}
        for item in items:
            if "=" not in item:
                raise ValueError(f"Extras must be KEY=VALUE, got '{item}'")
            key, value = item.split("=", 1)
            value = self.parse_value(value)
            d[key] = value
        return d
    
    def parse_dicts(self, args):
        args.extras = self.parse_dict(args.extras)

    def parse_base(self, args: argparse.Namespace) -> dict:
        unpacked = {}
        nested_keys = self.config_class.collect_nested_dataclasses()
        log.debug("Nested Keys %s" % nested_keys)

        for k, v in vars(args).items():
            if v is None:
                continue
            if "." in k:
                parts = k.split(".")
                if parts[0] not in nested_keys:
                    raise KeyError(f"Nested Key {parts[0]} detected but no corresponding dataclass exists!")
                if parts[0] in unpacked.keys():
                    unpacked[parts[0]][parts[1]] = v
                else:
                    unpacked[parts[0]] = {parts[1]:v}
            else:
                unpacked[k] = v
        return unpacked
    
    def parse_args(self, argv=None) -> TConfig:
        parser, args = self.build_parser(argv)
        
        self.parse_dicts(args)

        cli_args = self.parse_base(args)

        cfg = self.config_class.from_dict(cli_args) 
        cfg.cmd_args = cli_args
        return cfg


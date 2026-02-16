import logging
import argparse
from typing import Dict, Any, Tuple, Type, Callable, List

from .arguments import add_extra_params, add_config_params
from .config import BaseConfig

log = logging.getLogger(__name__)

ParamFunc = Callable[[argparse.ArgumentParser], None]


class BaseCLIParser:
    config_class: Type[BaseConfig]
    _param_funcs: List[ParamFunc]

    def __init__(self) -> None:
        self.config_class = BaseConfig # Overwrite this if you are using another Config!!
        self._param_funcs = [add_extra_params, add_config_params] # Add other functions to this list!

    def append_param_func(self, param_func: ParamFunc):
        self._param_funcs.append(param_func)

    def build_parser(self, argv) -> Tuple[argparse.ArgumentParser, argparse.Namespace]:
        parser = argparse.ArgumentParser(description="Run experiment")

        for param_func in self._param_funcs:
            param_func(parser)

        args, _ = parser.parse_known_args(argv)
        return parser, args



    def parse_extras(self, items) -> Dict[str, Any]:
        extras = {}
        for item in items:
            if "=" not in item:
                raise ValueError(f"Extras must be KEY=VALUE, got '{item}'")
            key, value = item.split("=", 1)
            extras[key] = value
        return extras

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
    
    def parse_args(self, argv=None) -> BaseConfig:
        parser, args = self.build_parser(argv)
        
        extras = self.parse_extras(args.extra)
        delattr(args, "extra")
        args.extras = extras

        cli_args = self.parse_base(args)
        cfg = self.config_class(**cli_args)
        cfg.cmd_args = cli_args
        return cfg
from dataclasses import dataclass, field
from typing import Tuple
from pathlib import Path
import logging

import sys


from foundation import BaseConfig, BaseCLIParser
from foundation import init_root_logger


@dataclass
class NestedDataClass:
    test_value_int: int = 5
    test_value_str: str = "Hello World"

@dataclass
class TestConfig(BaseConfig):
    test_value_int: int = 10
    test_value_str: str = "Hello World"

    nested: NestedDataClass = field(default_factory=NestedDataClass)

def add_test_params(parser):
    # Test Arguments
    parser.add_argument("--testPATH", type=Path, default=None, help="Testing Path")
    parser.add_argument("--testTUPLE", type=Tuple, default=None, help="Testing Tuple")


class CLIParser(BaseCLIParser):
    def __init__(self) -> None:
        super().__init__()
        self.config_class = TestConfig
        self.append_param_func(add_test_params)



def testing():
    init_root_logger()
    log = logging.getLogger()
    cli_parser = CLIParser()
    cfg: TestConfig = cli_parser.parse_args() # type: ignore
    log.debug(cfg.nested.test_value_int)
    cfg.cfg_file_name_save = cfg.cfg_file_name_load = "test"
    cfg.save()
    cfg2: TestConfig = TestConfig.cfg_load(cfg.get_cfg_file_path("load")) # type: ignore
    log.debug(cfg2)
    log.debug(cfg2.nested.test_value_int)
    


if __name__ == "__main__":
    sys.exit(testing())

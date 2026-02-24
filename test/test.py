from dataclasses import dataclass, field
from typing import Tuple, TypeVar, Type
from pathlib import Path
from datetime import datetime
import logging

import sys


from foundation import BaseConfig, BaseCLIParser
from foundation.log import init_root_logger
from foundation.utils import ensure_dir_exists


TConfig = TypeVar("TConfig", bound="BaseConfig")


@dataclass
class NestedDataClass:
    test_value_int: int = 5
    test_value_str: str = "Hello World"

@dataclass
class TestConfig(BaseConfig):
    test_value_int: int = 10
    test_value_str: str = "Hello World"
    test_date: datetime = datetime(2026,12,1)

    nested: NestedDataClass = field(default_factory=NestedDataClass)

def add_test_params(parser):
    # Test Arguments
    parser.add_argument("--testPATH", type=Path, default=None, help="Testing Path")
    parser.add_argument("--testTUPLE", type=Tuple, default=None, help="Testing Tuple")


class CLIParser(BaseCLIParser):
    def __init__(self, config_class: Type[TConfig]) -> None:
        super().__init__(config_class)
        self.config_class = TestConfig # Is this line even necessary now?
        self.append_param_func(add_test_params)



def testing():
    init_root_logger()
    log = logging.getLogger()
    cli_parser = CLIParser(TestConfig)
    cfg: TestConfig = cli_parser.parse_args()
    log.debug(cfg.nested.test_value_int)
    cfg.cfg_file_name_save = cfg.cfg_file_name_load = "test"
    cfg.save()
    cfg.cfg_file_name_save = None
    cfg.save(ensure_dir_exists(cfg.current_run_dir / "configs") / 'test2.json')
    cfg2: TestConfig = TestConfig.cfg_load(cfg.get_cfg_file_path("load"))
    log.debug(cfg2)
    log.debug(cfg2.nested.test_value_int)
    log.info(cfg2.json_encoder)
    


if __name__ == "__main__":
    sys.exit(testing())

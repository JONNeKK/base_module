from pathlib import Path
import argparse

from src.utils import str2bool
    

def add_extra_params(parser: argparse.ArgumentParser):
    # Controlled extras
    parser.add_argument(
        "--extra",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Optional extra parameters (explicit opt_in)"
    )

def add_config_params(parser: argparse.ArgumentParser):
    # File Context
    parser.add_argument("--cfg_save_dir", type=Path, default=None, help="Config save directory")
    parser.add_argument("--current_run_dir", type=Path, default=None, help="Current run directory")

    # Config
    parser.add_argument("--cfg_file_name", type=str, default=None, help="Config file name")
    parser.add_argument("--override_from_cmd", type=str2bool, default=None, help="Override from command line")
    # cmd_args will be populated later, no CLI argument

    # Debug Flags
    parser.add_argument("--debug", action="store_true", help="Debug mode")
    
    # Logging
    parser.add_argument("--log_dir", type=str, default=None, help="Log directory")
    parser.add_argument("--log_level", type=int, default=None, help="Logging level")

import logging
from colorlog import ColoredFormatter
from pathlib import Path
from typing import Union




# Add custom log level
INFOV_LEVEL = 15  # between DEBUG (10) and INFO (20)
logging.addLevelName(INFOV_LEVEL, "INFOV")

def infov(self, message, *args, **kwargs) -> None:
    if self.isEnabledFor(INFOV_LEVEL):
        self._log(INFOV_LEVEL, message, args, **kwargs)

logging.Logger.infov = infov # type: ignore


def create_formatter(colour: bool) -> Union[ColoredFormatter,logging.Formatter]:
    if colour:
        return ColoredFormatter(
            "%(log_color)s[%(asctime)s][%(process)05d] %(message)s",
            datefmt=None,
            reset=True,
            log_colors={
                "DEBUG": "cyan",
                "INFO": "white,bold",
                "INFOV": "cyan,bold",
                "WARNING": "yellow",
                "ERROR": "red,bold",
                "CRITICAL": "red,bg_white",
            },
            secondary_log_colors={},
            style="%",
        )
    else:
        return logging.Formatter(fmt="[%(asctime)s][%(process)05d] %(message)s", datefmt=None, style="%")

def create_file_handler(path: Path, level) -> logging.FileHandler:
    file_handler = logging.FileHandler(path)
    file_handler.setLevel(level)
    file_handler.setFormatter(create_formatter(colour = False))
    return file_handler

def create_stream_handler() -> logging.StreamHandler:
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(create_formatter(colour = True))
    return stream_handler


def add_file_handler(log:logging.Logger, path: Path):
    if has_file_handler(log):
        log.warning("A File Handler already exists! Weird! Adding anyways")
    log.addHandler(create_file_handler(path, log.getEffectiveLevel()))

def add_stream_handler(log:logging.Logger, path: Path):
    if has_stream_handler(log):
        log.warning("A Stream Handler already exists! Weird! Adding anyways")
    log.addHandler(create_stream_handler())
    


def has_file_handler(log: logging.Logger) -> bool:
    for handler in log.handlers:
        if isinstance(handler, logging.FileHandler):
            return True
    return False

def has_stream_handler(log: logging.Logger) -> bool:
    for handler in log.handlers:
        if isinstance(handler, logging.StreamHandler):
            return True
    return False


def init_root_logger(default_level = logging.DEBUG):
    logger = logging.getLogger()
    logger.setLevel(default_level)
    # Create and configure the stream (console) handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(create_formatter(colour = True))
    logger.addHandler(stream_handler)


import logging
from colorlog import ColoredFormatter
from pathlib import Path
from typing import cast

log = logging.getLogger(__name__)


# Add custom log level
INFOV_LEVEL = 15  # between DEBUG (10) and INFO (20)
logging.addLevelName(INFOV_LEVEL, "INFOV")

def infov(self, message, *args, **kwargs) -> None:
    if self.isEnabledFor(INFOV_LEVEL):
        self._log(INFOV_LEVEL, message, args, **kwargs)

logging.Logger.infov = infov # type: ignore

PACKAGE_LOGGER = "foundation"
DEFAULT_FILE_HANDLER = "default_file"
DEFAULT_STREAM_HANDLER = "default_stream"
DEFAULT_FORMAT = "[{asctime}][{process:05d}][{module:.<10.10}][{lineno:04d}] {message}"

def _create_formatter(
        *,
        colour: bool,
        fmt: str = DEFAULT_FORMAT,
    ) -> logging.Formatter:
    if colour:
        return ColoredFormatter(
            "{log_color}" + fmt,
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
            style="{",
        )
    else:
        return logging.Formatter(fmt=fmt, datefmt=None, style="{")

def _get_handler_by_name(
        logger: logging.Logger,
        name: str | None = None,
    ) -> logging.Handler | None:
    """
    Returns the first handler with the specified name 
    or None (if no handler with that name exists)
    """
    return next(
        (handler for handler in logger.handlers if handler.name == name),
        None,
    )

def _create_and_configure_stream_handler(
        *,
        level: int,
        colour: bool,
        name: str = DEFAULT_STREAM_HANDLER,
        fmt: str = DEFAULT_FORMAT,
    ) -> logging.StreamHandler:
    
    handler = logging.StreamHandler()
    handler.name = name

    handler.setLevel(level)
    handler.setFormatter(_create_formatter(colour=colour, fmt=fmt))
    return handler

def _create_and_configure_file_handler(
        *,
        path: Path,
        level: int,
        name: str = DEFAULT_FILE_HANDLER,
        fmt: str = DEFAULT_FORMAT,
    ) -> logging.FileHandler:
    
    handler = logging.FileHandler(path)
    handler.name = name

    handler.setLevel(level)
    handler.setFormatter(_create_formatter(colour=False, fmt=fmt))
    return handler

def add_file_handler(
        logger:logging.Logger, 
        path: Path, 
        level: int, 
        name: str = DEFAULT_FILE_HANDLER, 
        fmt=DEFAULT_FORMAT
    ):
    
    handler = _get_handler_by_name(logger, name)

    if handler is None:
        handler = _create_and_configure_file_handler(path=path, level=level, name=name, fmt=fmt)
        logger.addHandler(handler)
    else:
        log.warning("FileHandler with name %s already exists! Not adding again." % name)

def add_stream_handler(
        logger:logging.Logger, 
        level: int, 
        colour: bool, 
        name: str = DEFAULT_STREAM_HANDLER, 
        fmt=DEFAULT_FORMAT):
    
    handler = _get_handler_by_name(logger, name)

    if handler is None:
        handler = _create_and_configure_stream_handler(level=level, colour=colour, name=name, fmt=fmt)
        logger.addHandler(handler)
    else:
        log.warning("StreamHandler with name %s already exists! Not adding again." % name)

def remove_handler(
        logger: logging.Logger,
        name: str,
    ) -> None:
    handler = cast(logging.Handler, _get_handler_by_name(logger, name)) # name is defined. Could be either 

    if handler is not None:
        logger.removeHandler(handler)
        handler.close()
    else:
        log.info("No Handler with the name %s exists. Cannot remove." % name)


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


def configure_logging(
        logger: logging.Logger | None = None,
        *,
        level: int = logging.INFO,
        log_file: Path | None = None,
        colour: bool = True,
        fmt: str = DEFAULT_FORMAT,
    ) -> None:
    """
    Configure sensible logging defaults for the given logger.

    If logger is omitted, configures the root logger.

    Calling this multiple times is safe.
    """
    if logger is None:
        logger = logging.getLogger()

    # The logger must allow everything the handlers might want.
    logger.setLevel(logging.DEBUG)

    add_stream_handler(
        logger=logger,
        level=level,
        colour=colour,
        fmt=fmt,
    )

    if log_file is not None:
        add_file_handler(
            logger=logger,
            path=log_file,
            level=logging.DEBUG,
            fmt=fmt,
        )

# Enable, Disable logging for BaseModule
def enable_logging() -> None:
    logger = logging.getLogger(PACKAGE_LOGGER)
    logger.propagate = True


def disable_logging() -> None:
    logger = logging.getLogger(PACKAGE_LOGGER)
    logger.propagate = False

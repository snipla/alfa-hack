import logging
import os
from dataclasses import dataclass


@dataclass
class Colors:
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


class ConsoleFormatter(logging.Formatter):
    def format(self, record):
        lvl = record.levelname
        colored = lvl
        if lvl == "INFO":
            colored = f"{Colors.BOLD}{Colors.GREEN}[I]{Colors.RESET}"
        elif lvl == "WARNING":
            colored = f"{Colors.BOLD}{Colors.YELLOW}[W]{Colors.RESET}"
        elif lvl == "DEBUG":
            colored = f"{Colors.BOLD}{Colors.BLUE}[D]{Colors.RESET}"
        elif lvl == "ERROR":
            colored = f"{Colors.BOLD}{Colors.RED}[E]{Colors.RESET}"

        record.levelname = colored
        out = super().format(record)
        record.levelname = lvl
        return out


class FileFormatter(logging.Formatter):
    def format(self, record):
        lvl = record.levelname
        short = lvl
        if lvl == "INFO":
            short = "[I]"
        elif lvl == "WARNING":
            short = "[W]"
        elif lvl == "DEBUG":
            short = "[D]"
        elif lvl == "ERROR":
            short = "[E]"

        record.levelname = short
        out = super().format(record)
        record.levelname = lvl
        return out


def init_app_logging():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    root_logger.handlers = []

    console_formatter = ConsoleFormatter(
        "%(levelname)s " + Colors.WHITE + "%(message)s" + Colors.RESET
    )

    log_path = os.path.join("logs", "app.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(console_formatter)

    root_logger.addHandler(ch)

    intercept_loggers = ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi")

    for logger_name in intercept_loggers:
        sub_logger = logging.getLogger(logger_name)
        sub_logger.handlers = []
        sub_logger.propagate = True

    noisy_loggers = (
        "aioimaplib",
        "httpx",
        "httpcore",
        "urllib3",
        "botocore",
        "aiobotocore",
        "s3transfer",
        "boto3",
    )
    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

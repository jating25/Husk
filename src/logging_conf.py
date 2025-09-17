# src/logging_conf.py
import logging
from rich.logging import RichHandler

def setup_logging(level="INFO"):
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
        handlers=[RichHandler()]
    )
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    return logging.getLogger("husk")

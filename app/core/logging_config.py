import logging
from typing import Optional

def configure_logging(level: int = logging.INFO, log_file: Optional[str] = None) -> None:
    """
    Configure logging for the application.
    Args:
        level (int): Logging level (default: logging.INFO)
        log_file (Optional[str]): If provided, log to this file as well as stdout.
    """
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers
    ) 
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from rich.logging import RichHandler

def setup_logging(log_level: str = "INFO", log_file: str = "logs/installation_agent.log"):
    """
    Sets up professional logging to both the console (with Rich formatting) 
    and a rotating log file in the logs directory.
    """
    # Ensure directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Clear existing handlers on root to avoid duplicate logs
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    # Configure handlers
    # Console handler using Rich for beautiful colored output
    console_handler = RichHandler(
        rich_tracebacks=True,
        markup=True,
        show_path=False
    )
    console_handler.setLevel(log_level)
    
    # Rotating file handler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024, # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(log_level)
    
    # File formatter
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    # Setup root logger
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[console_handler, file_handler]
    )
    
    # Set levels for noisy libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("watchdog").setLevel(logging.WARNING)
    
    logger = logging.getLogger("installation_agent")
    logger.info(f"Logging initialized at level [bold cyan]{log_level}[/bold cyan]. Log file: [underline]{log_file}[/underline]")
    return logger

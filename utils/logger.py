import logging
import os
from logging.handlers import RotatingFileHandler

def get_logger(name: str, logs_dir: str = "logs", max_bytes: int = 50 * 1024 * 1024, backup_count: int = 5) -> logging.Logger:
    """
    Create and return a logger with rotating file handler.
    
    Args:
        name (str): Logger name, also used as filename.
        logs_dir (str): Directory to store log files. Default = 'logs'.
        max_bytes (int): Max size of log file before rotation. Default = 50MB.
        backup_count (int): Number of backup log files to keep. Default = 5.

    Returns:
        logging.Logger: Configured logger instance.
    """
    # Ensure logs directory exists
    os.makedirs(logs_dir, exist_ok=True)
    
    # Log file path
    log_file = os.path.join(logs_dir, f"{name}.log")
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Can be adjusted
    
    # Prevent duplicate handlers if called multiple times
    if not logger.handlers:
        # Rotating file handler
        handler = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
        )
        
        # Log format
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
    
    return logger

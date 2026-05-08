from loguru import logger
import sys

def setup_logging():
    logger.remove()
    
    logger.add(
        sys.stdout,
        format="{time:HH:mm:ss} | {level: <7} | {message} {extra}",
        level="INFO",
        enqueue=True
    )
    
    logger.add(
        "logs/info.log",
        level="INFO",
        rotation="30 MB",
        retention="10 days",
        compression="zip",
        enqueue=True
    )
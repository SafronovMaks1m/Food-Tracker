from loguru import logger
import sys

def setup_logging():
    logger.remove()
    
    logger.add(
        sys.stdout,
        format="<white>{time:HH:mm:ss}</white> | <level>{level: <7}</level> | <cyan>{message}</cyan> {extra}",
        level="INFO",
        enqueue=True,
        colorize=True
    )
    
    logger.add(
        "logs/info.log",
        level="INFO",
        rotation="30 MB",
        retention="10 days",
        compression="zip",
        enqueue=True
    )
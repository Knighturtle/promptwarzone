import logging
import os

LOG_PATH = os.getenv("LOG_PATH", "logs/app.log")

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("bbs")

def log_info(msg):
    logger.info(msg)

def log_error(msg):
    logger.error(msg)


import logging
from logging.handlers import RotatingFileHandler
import os 

LOG_FILE_NAME = "bot.log"
PORT = os.environ.get("PORT", "8091")

OWNER_ID = 8497538010
MSG_EFFECT = 5046509860389126442

SHORT_URL = ""
SHORT_API = ""

def LOGGER(name: str, client_name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    formatter = logging.Formatter(
        f"[%(asctime)s - %(levelname)s] - {client_name} - %(name)s - %(message)s",
        datefmt='%d-%b-%y %H:%M:%S'
    )
    
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        logger.addHandler(stream_handler)

    return logger

LOGS = logging.getLogger("Bot")
LOGS.setLevel(logging.INFO)
LOGS.addHandler(logging.StreamHandler())

class Var:
    ADMINS = [int(x) for x in os.environ.get("ADMINS", str(OWNER_ID)).split()]
    QUALS = ["HDRip", "1080", "720", "480"]
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "-1002235957011"))

    CUSTOM_BANNER = os.environ.get("CUSTOM_BANNER", "https://ibb.co/5xjBCXKp")
    AS_DOC = os.environ.get("AS_DOC", "False").lower() == "true"


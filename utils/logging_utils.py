import json
import logging
import traceback
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

import discord

from config import LOG_FILE


def setup_logger(logger_name: str) -> logging.Logger:
    """
    Take in a logger_name and generate a logger with the follow properties:
    - Formatter of format [%(asctime)s] - [%(levelname)s] - [%(message)s] - [%(name)s]
    - Log info level to a central LOG_FILE
    - Log warning level to stream
    :return logger: An object of type Logger with the name of logger_name
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    # Future reference: https://www.futurefundamentals.com/how-to-setup-custom-logging-in-pythonflask-with-dictconf-way/
    formatter = logging.Formatter(
        "[%(asctime)s] - [%(levelname)s] - [%(message)s] - [%(name)s]", datefmt="%Y-%m-%d %H:%M:%S %Z")

    # file_handler = TimedRotatingFileHandler(
    #     filename=LOG_FILE, when='M', utc=True, interval=1, backupCount=10)
    file_handler = RotatingFileHandler(
        filename=LOG_FILE, maxBytes=1000000, backupCount=10)
    # if not DEBUG:
    #     file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger


def unexpected_error_handler(logger: logging.Logger, e: Exception, **kwargs):
    logger.error(f"""
==================== Unexpected Error ===================
Unexpected: {e}, {type(e)}"
---------------------------------------------------------
Variables: {json.dumps(kwargs, indent=4)}
---------------------------------------------------------
Traceback: {traceback.format_exc()}
=========================================================
""")

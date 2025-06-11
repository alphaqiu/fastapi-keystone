import logging

from fastapi_keystone.config import Config


def setup_logger(config: Config):
    formatter = "%(asctime)s.%(msecs)03d |%(levelname)s| %(name)s.%(funcName)s:%(lineno)d |logmsg| %(message)s"
    if config.logger.format:
        formatter = config.logger.format
    level = config.logger.level
    log_level: int = getattr(logging, level.upper()) or logging.INFO
    logging.basicConfig(
        level=log_level,
        format=formatter,
        force=True,
    )

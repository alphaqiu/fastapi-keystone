import logging

from fastapi_keystone.config import Config


def setup_logger(config: Config):
    formatter = "%(asctime)s.%(msecs)03d |%(levelname)s| %(name)s.%(funcName)s:%(lineno)d |logmsg| %(message)s"
    if config.logger.format:
        formatter = config.logger.format
    level = config.logger.level
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format=formatter,
        force=True,
    )

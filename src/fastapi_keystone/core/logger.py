import logging

from fastapi_keystone.config import Config


def setup_logger(config: Config):
    formatter = "%(asctime)s.%(msecs)03d |%(levelname)s| %(name)s.%(funcName)s:%(lineno)d |logmsg| %(message)s"
    if config.logger.format and config.logger.format != "":
        formatter = config.logger.format
    level = config.logger.level
    str_level = getattr(logging, level.upper())
    if not str_level or str_level not in logging._nameToLevel.keys():
        level = "INFO"
    log_level: int = logging._nameToLevel[level]
    print(f"log_level: {log_level}, formatter: {formatter}")
    logging.basicConfig(
        level=log_level,
        format=formatter,
        force=True,
    )

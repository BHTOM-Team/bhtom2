from logging import Logger, getLogger
from django.conf import settings
import inspect


class BHTOMLogger:

    def __init__(self, name, log_prefix: str):
        self.__logger: Logger = getLogger(name)
        self.__log_prefix: str = log_prefix
        self.__graylog_host: str = settings.GRAYLOG_HOST

    def info(self, message: str):
        frame = inspect.currentframe().f_back
        lineno = frame.f_lineno

        self.__logger.info(f'[{self.__log_prefix}:{lineno}] - {message}')

    def debug(self, message: str):
        frame = inspect.currentframe().f_back
        lineno = frame.f_lineno
        self.__logger.debug(f'[{self.__log_prefix}:{lineno}] - {message}')

    def warning(self, message: str):
        frame = inspect.currentframe().f_back
        lineno = frame.f_lineno
        self.__logger.warning(f'[{self.__log_prefix}:{lineno}] - {message}')

    def error(self, message: str):
        frame = inspect.currentframe().f_back
        lineno = frame.f_lineno
        self.__logger.error(f'[{self.__log_prefix}:{lineno}] - {message}')

    def exception(self, message: Exception):
        frame = inspect.currentframe().f_back
        lineno = frame.f_lineno
        self.__logger.exception(f'[{self.__log_prefix}:{lineno}] - {message}')

import traceback
from enum import Enum
from threading import Lock
from typing import Optional


class Level(Enum):
    ROUTINE = 1
    WARNING = 2
    ERROR = 3

    def relative_value(self) -> int:
        return int(self.value)

    @classmethod
    def from_name(cls, level_name: str) -> Optional['Level']:

        for level in Level:
            if level.name == level_name:
                return level

        return None

class Logger:

    logger_instance = None

    thread_lock = Lock()

    @classmethod
    def log(cls, message: str, level: Level = Level.ROUTINE):
        cls.get_logger()._log_message(level, message)

    # noinspection PyUnusedLocal
    @classmethod
    def log_exception(cls, message: str, exception: Exception, level: Level = Level.ERROR):

        logger = cls.get_logger()

        logger._log_message(level, message + ':')

        # note: traceback gives the full message from the last thrown exception (which should match the exception param)
        full_exception_message = traceback.format_exc()
        logger._log_message(level, full_exception_message)

    @classmethod
    def create_logger(cls, log_to_console: bool, log_filename: str = None):
        """
        Create a logger instance suitable for the remainder of the application execution. Ideally this will be called
        before get_logger, but if not then a default logger will be created temporarily.

        :param log_to_console: True if log messages should be written to application console
        :param log_filename: the full path to the file to which messages will be logged *if* log_to_console is False
        :return:
        """
        with cls.thread_lock:
            cls.logger_instance = Logger(log_to_console, log_filename)

    @classmethod
    def get_logger(cls):
        """
        Ideally this method would not be called before create_logger is called. If that is true then the instance from
        the one create_logger call will be returned. However, to allow logging before then, a temporary logger instance
        will be created (with default options) and returned, if necessary.

        :return: the single shared logger instance
        """

        with cls.thread_lock:

            # if an instance has already been created, either by a prior call to get_logger or create_logger, then
            # return the instance
            if cls.logger_instance:
                return cls.logger_instance

            # if this method is called before create_logger, we still want to return a working logger of some kind.

            cls.logger_instance = Logger()

            return cls.logger_instance

    def __init__(
            self,
            to_console: bool = True,
            log_file_name: str|None = None,
            log_level: Level = Level.ROUTINE
    ):

        self.to_console = to_console
        self.log_file_name = log_file_name
        self.log_level = log_level

    def change_level(self, log_level: Level):
        self.log_level = log_level

    def _log_message(self, level: Level, message):

        # note: technically, we should be taking the thread lock here to avoid testing the log level while another
        # thread might be changing it. however, taking a thread lock is relatively expensive and the logging level
        # will be changing almost never. better to take the risk rather than having even routine logging be expensive.

        # don't log if level doesn't exceed current configuration
        if self.log_level.relative_value() > level.relative_value():
            return

        with self.thread_lock:

            if self.to_console:
                print(message)
            else:
                with open(self.log_file_name, 'a') as open_log_file:
                    print(message, file=open_log_file)
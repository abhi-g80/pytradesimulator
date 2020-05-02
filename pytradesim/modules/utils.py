import logging
import quickfix as fix

from datetime import datetime


class LogFormat(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        log_time = datetime.fromtimestamp(record.created)
        microseconds = "{0:.6f}".format(record.created).rsplit(".")[1]
        formatted_logline = f"{log_time.strftime('%Y-%m-%d %H:%M:%S')}.{microseconds}"

        return formatted_logline

    def format(self, record):
        indent = "\n    "
        msg = logging.Formatter.format(self, record)

        return indent.join([line for line in msg.split("\n")])


def setup_logging(log_path, file_name):
    log_formatter = LogFormat(
        fmt="%(asctime)s [%(levelname)-7.7s] (%(funcName)-9.9s) %(message)s"
    )
    root_logger = logging.getLogger()

    file_handler = logging.FileHandler("{0}/{1}.log".format(log_path, file_name))
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    return root_logger


class Message(fix.Message):
    def __str__(self):
        message = super().__str__()
        return message.replace("\x01", "|")

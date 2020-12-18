import socket
import threading

from src import tables
from src.logger import logger
from src.database import database

from functools import wraps

def lazy_init(init):
    import inspect
    arg_names = inspect.getargspec(init)[0]

    @wraps(init)
    def new_init(self, *args):
        for name, value in zip(arg_names[1:], args):
            setattr(self, name, value)
        init(self, *args)

    return new_init

class OneWayThread(threading.Thread):
    @lazy_init
    def __init__(self, source, dest, connection, config, direction):
        super().__init__()

        self.length = self.config.get(self.direction + '_length', 4096)
        self.lines = self.config.get(self.direction + '_lines', 10)

        self.shutdown_requested = False

    def read(self):
        logger.debug(self.direction + ' reading from: ' + str(self.source))
        data = self.source.recv(4096)
        logger.debug(self.direction + ' read: ' + str(data))

        return data

    def write(self, data):
        logger.debug(self.direction + ' sending to: ' + str(self.dest))
        self.dest.sendall(data)
        logger.debug(self.direction + ' sent: ' + str(data))

    def too_many_lines(self, data):
        if self.lines > 0:
            s = str(data)
            count = 0
            delims = self.direction + 'delimiters'
            if delims in self.config:
                for end in config[delims]:
                    count = max(count, s.count(line_end))
                if count >= self.lines:
                    logger.info('Lines exceeded, stopping')
                    return True
        return False

    def run(self):
        total = b''
        while True:
            try:
                data = self.read()
                if not data or data == b'':
                    break
                self.write(data)
            except Exception as exception:
                logger.info(self.direction + " " + str(exception))
                break

            total += data

            if self.shutdown_requested:
                break

            if self.length > 0 and len(total) >= self.length:
                logger.debug('Length exceeded')
                break

            if too_many_lines(data):
                break

        logger.debug(self.length)
        logger.debug(len(total))
        logger.debug(self.direction)
        if self.length > 0 and len(total) > 0:
            database.write(tables.Data(direction=self.direction, data=str(total), connection=self.connection))
        self.source.close()
        self.dest.close()

    def shutdown(self):
        self.shutdown_requested = True

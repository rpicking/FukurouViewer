import logging


class Logger(object):
    @property
    def logger(self) -> logging.Logger:
        try:
            name = '.'.join([self.__class__.__name__, self.name])
        except AttributeError:
            name = '.'.join([self.__class__.__name__])
        return logging.getLogger(name)

from enum import IntEnum

from pyingx import lib


class Level(IntEnum):
    INFO = 0
    WARN = 1
    ERROR = 2

_global_level = Level.INFO


def set_global_level(level):
    assert isinstance(level, Level)
    global _global_level
    _global_level = level


def get_global_level():
    return _global_level


class Logger(object):
    def __init__(self, level=None):
        if not level:
            self._level = None
        else:
            self._level = level

    def warn(self, msg):
        if (self._level or _global_level) <= Level.WARN:
            print "WARN: " + msg

    def error(self, msg):
        if (self._level or _global_level) <= Level.ERROR:
            print "ERROR: " + msg

    def info(self, msg):
        if (self._level or _global_level) <= Level.INFO:
            print "INFO: " + msg

    def set_level(self, level):
        assert isinstance(level, Level) or None
        self._level = level

    def get_level(self):
        return self._level or _global_level

LOG = Logger()

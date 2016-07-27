import eventlet
eventlet.monkey_patch(os=False)

from pyingx import server
from pyingx import config


def main():
    config.setup()
    server.launch()

import datetime
import websocket
import logging
import json

_logger = logging.getLogger(__name__)


class Socket():
    def __init__(self, on_message, on_close, url, token):
        pass

    def on_error(self, error):
        pass

    def on_close(self):
        pass

    def run(self):
        pass

    def send_msg(self, msg):
        pass

    def connected(self):
        pass

    def connect(self, on_message, on_close, url, token):
        pass

    def disconnect(self):
        pass
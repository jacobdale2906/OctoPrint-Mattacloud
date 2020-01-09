import json
import logging

import websocket

_logger = logging.getLogger("octoprint.plugins.mattacloud")


class Socket():
    def __init__(self, on_open, on_message, on_close, url, token):
        self.socket = websocket.WebSocketApp(url,
                                             on_open=on_open,
                                             on_message=on_message,
                                             on_close=on_close,
                                             on_error=self.on_error,
                                             header=[
                                                 "authorization: token {}".format(token)
                                             ]
                                             )

    def on_error(self, error):
        # TODO: handle websocket errors
        _logger.error(error)

    def on_close(self):
        # TODO: handle websocket errors
        _logger.debug("Closing the websocket...")
        self.disconnect()

    def run(self):
        self.socket.run_forever()

    def send_msg(self, msg):
        if isinstance(msg, dict):
            msg = json.dumps(msg)
        self.socket.send(msg)

    def connected(self):
        _logger.debug("The websocket is connected.")
        return self.socket.sock and self.socket.sock.connected

    def connect(self, on_message, on_close, url, token):
        self.socket = websocket.WebSocketApp(url,
                                             on_message=on_message,
                                             on_close=on_close,
                                             on_error=self.on_error,
                                             header=[
                                                 "authorization: token {}".format(token)
                                             ]
                                             )

    def disconnect(self):
        _logger.debug("Disconnecting the websocket...")
        self.socket.keep_running = False
        self.socket.close()
        _logger.debug("The websocket has been closed.")

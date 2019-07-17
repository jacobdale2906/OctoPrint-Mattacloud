#!/usr/bin/python
# -*- coding: utf-8 -*-
# coding = utf - 8

from __future__ import absolute_import

import time
import json
import threading
from urlparse import urljoin

import octoprint.plugin

from .watcher import ImageHandler
from .ws import Socket


class MattacloudPlugin(octoprint.plugin.StartupPlugin,
                       octoprint.plugin.SettingsPlugin,
                       octoprint.plugin.TemplatePlugin,
                       octoprint.plugin.AssetPlugin,
                       octoprint.plugin.SimpleApiPlugin,
                       octoprint.plugin.EventHandlerPlugin):

    def get_settings_defaults(self):
        return dict(
            base_url="https://mattalabs.com/",
            authorization_token="e.g. w1il4li2am2ca1xt4on91",
            enabled=True,
        )

    def get_assets(self):
        return dict(
            js=['js/mattacloud.js'],
            css=['css/mattacloud.css'],
            less=['less/mattacloud.less']
        )

    def get_template_configs(self):
        self._logger.info("OctoPrint-Mattacloud - is loading template configurations.")
        return [
            dict(type="settings", custom_bindings=False)
        ]

    def get_update_information(self):
        return dict(mattacloud=dict(
            displayVersion=self._plugin_version,
            type='github_release',
            user='dougbrion',
            repo='OctoPrint-Mattacloud',
            current=self._plugin_version,
            pip='https://github.com/dougbrion/OctoPrint-Mattacloud/archive/{target_version}.zip',
        ))

    def get_printer_data(self):
        self._logger.info("Fetching printer data")
        return self._printer.get_current_data()

    def get_current_job(self):
        self._logger.info("Fetching job data")
        return self._printer.get_current_job()

    def get_printer_temps(self):
        self._logger.info("Fetching temperature data")
        return self._printer.get_current_temperatures()

    def get_files(self):
        self._logger.info("Fetching file list")
        return self._file_manager.list_files(recursive=True)

    def get_base_url(self):
        if not self._settings.get(["base_url"]):
            self._logger.info("No base URL in OctoPrint settings")
            return None

        url = self._settings.get(["base_url"])
        url = url.strip()
        if url.startswith("/"):
            url = url[1:]
        if url.endswith("/"):
            url = url[:-1]
        return url

    def get_api_url(self):
        base_url = self.get_base_url()
        url = urljoin(base_url, "api")
        return url

    def get_ws_url(self):
        api_url = self.get_api_url()
        url = urljoin(api_url, "ws", "printer")
        url = url.replace("http", "ws")
        return url

    def get_ping_url(self):
        api_url = self.get_api_url()
        url = urljoin(api_url, "ping")
        return url

    def get_data_url(self):
        api_url = self.get_api_url()
        url = urljoin(api_url, "receive", "data")
        return url

    def get_img_url(self):
        api_url = self.get_api_url()
        url = urljoin(api_url, "receive", "img")
        return url

    def get_gcode_url(self):
        api_url = self.get_api_url()
        url = urljoin(api_url, "receive", "gcode")
        return url

    def get_request_url(self):
        api_url = self.get_api_url()
        url = urljoin(api_url, "receive", "request")
        return url

    def get_auth_token(self):
        if not self._settings.get(["authorization_token"]):
            return None
        return self._settings.get(["authorization_token"])

    def make_auth_header(self, token=None):
        if not token:
            token = self.get_auth_token()
        return {
            self.auth_token_header(token),
        }

    def auth_token_header(self, token=None):
        if not token:
            token = self.get_auth_token()
        return "Authorization: Token {}".format(token)

    def on_after_startup(self):
        self._logger.info("Starting OctoPrint-Mattacloud Plugin...")
        self.img_lst = []
        self.len_img_lst = 0
        self.new_print_job = False
        self.ws = None

    def on_event(self, event, payload):
        self._logger.info("Event: " + str(event))
        self._logger.info("Payload: " + str(payload))

    def event_ws_data(self, event, payload):
        data = self.ws_data()
        data["event"] = {
            "event_type": event,
            "payload": payload
        }
        return data

    def event_post_data(self, event, payload):
        data = {
            "event": {
                "event_type": event,
                "payload": payload
            },
            "printer_data": self.get_printer_data(),
            "temperature_data": self.get_printer_temps(),
            "timestamp": self.make_timestamp(),
        }
        return data

    def is_enabled(self):
        return self._settings.get(["enabled"])

    def is_operational(self):
        return self._printer.is_ready() or self._printer.is_operational()

    def is_setup_complete(self):
        return self.get_base_url() and self.get_auth_token()

    def ws_connect(self):
        self._logger.info("Connecting websocket")
        self.ws = Socket(on_message=lambda ws, msg: self.ws_on_message(ws, msg),
                         on_close=lambda ws: self.ws_on_close(ws),
                         url=self.get_ws_url(),
                         token=self.get_auth_token())
        ws_thread = threading.Thread(target=self.ws.run)
        ws_thread.daemon = True
        ws_thread.start()
        self._logger.info("Started websocket")

    def ws_on_close(self, ws):
        self._logger.info("Closing websocket...")
        self.ws.disconnect()
        self.ws = None

    def ws_on_message(self, ws, msg):
        self._logger.info("Message... {}".format(msg))
        json_msg = json.loads(msg)
        if "cmd" in json_msg:
            self.handle_cmds(json_msg)

    def ws_data(self):
        # TODO: Customise what is sent depending on requirements
        data = {
            "temperature_data": self.get_printer_temps(),
            "printer_data": self.get_printer_data(),
            "timestamp": self.make_timestamp(),
            "files": self.get_files(),
            "job": self.get_current_job(),
        }
        return data

    def handle_cmds(self, json_msg):
        pass

    def loop(self):
        while True:
            if self.is_enabled():
                if not is_setup_complete():
                    self._logger.warning("Invalid URL or Authorisation Token")
                    time.sleep(1)
                    next

            if self.ws:
                msg = self.ws_data()
                self.ws.send_msg(msg)

            if self.len_img_lst < len(self.img_lst):
                pass

            time.sleep(1)

__plugin_name__ = 'Mattacloud'


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = MattacloudPlugin()
    global __plugin_hooks__
    __plugin_hooks__ = {
        'octoprint.plugin.softwareupdate.check_config': __plugin_implementation__.get_update_information
    }

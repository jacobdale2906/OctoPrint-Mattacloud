#!/usr/bin/python
# -*- coding: utf-8 -*-
# coding = utf - 8

from __future__ import absolute_import

import os
import time
import json
import threading
import requests
import datetime
import flask
import cgi
import io
from urlparse import urljoin
from watchdog.observers import Observer

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
            snapshot_dir="/home/pi/.octoprint/data/octolapse/snapshots/",
            upload_dir="/home/pi/.octoprint/uploads/",
            snapshot_count=0,
            enabled=True,
            config_print=False,
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
        main_thread = threading.Thread(target=self.loop)
        main_thread.daemon = True
        main_thread.start()
        dir_path = self.get_octolapse_dir()
        watchdog_thread = threading.Thread(
            target=self.run_observer, args=(dir_path,))
        watchdog_thread.daemon = True
        watchdog_thread.start()
        self.ws_connect()

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

    def is_config_print(self):
        return self._settings.get(["config_print"])

    def has_job(self):
        if (self._printer.is_printing() or
            self._printer.is_paused() or
                self._printer.is_pausing()):
            return True
        return False

    def get_snapshot_dir(self):
        if not self._settings.get(["snapshot_dir"]):
            return None
        return self._settings.get(["snapshot_dir"])

    def get_octolapse_dir(self, dir_path=None):
        if not dir_path:
            dir_path = self.get_snapshot_dir()
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        return dir_path

    def get_latest_img_path(self, img_path):
        self.current_img_path = img_path

    def set_snapshot_count(self, count):
        self._settings.set(["snapshot_count"], count, force=True)
        self._settings.save(force=True)

    def run_observer(self, dir_path):
        event_handler = ImageHandler(self.img_lst)
        observer = Observer()
        observer.schedule(event_handler, path=dir_path, recursive=True)
        observer.start()

        try:
            while True:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit) as ex:
            self._logger.warning("Exception Handling")
            observer.stop()

        observer.join()

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

    def make_timestamp(self):
        dt = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        return dt

    def post_gcode(self, gcode=None):
        self._logger.info("Posting gcode")
        if not self.is_setup_complete():
            self._logger.warning("Printer not ready")
            return

        data = {
            "timestamp": self.make_timestamp(),
            "config": 1 if self.is_config_print() else 0,
        }

        if not gcode:
            job_info = self.get_current_job()
            gcode_name = job_info.get("file", {}).get("name")
            upload_dir = self._settings.get(["upload_dir"])
            path = upload_dir + gcode_name
            gcode = open(path, "rb")

        url = self.get_gcode_url()

        files = {
            "gcode": gcode,
        }

        resp = requests.post(
            url=url,
            files=files,
            data=data,
            headers=self.get_auth_headers_dict()
        )
        resp.raise_for_status()

    def post_img(self, img=None):
        self._logger.info("Posting image")
        if not self.is_setup_complete():
            self._logger.info("Printer not ready")
            return

        url = self.get_img_url()

        files = {
            "img": img,
        }

        data = {
            "timestamp": self.make_timestamp(),
        }
        resp = requests.post(
            url=url,
            files=files,
            data=data,
            headers=self.get_auth_headers_dict()
        )
        resp.raise_for_status()

    def post_data(self, data=None):
        self._logger.info("Posting data")
        if not self.is_setup_complete():
            self._logger.warning("Printer not ready")
            return

        if not data:
            data = {
                "timestamp": self.make_timestamp(),
                "data": self.get_printer_data(),
            }

        url = self.get_data_url()

        resp = requests.post(
            url=url,
            data=data,
            headers=self.get_auth_headers_dict()
        )
        resp.raise_for_status()
        self.process_response(resp)

    def is_new_job(self):
        if self.has_job():
            if self.new_print_job:
                self._logger.info("New job")
                self.post_gcode()
                self.new_print_job = False
        elif self.is_operational():
            self.new_print_job = True
            if self.img_lst != []:
                del self.img_lst[:]
                self.len_img_lst = 0
                self.set_snapshot_count(0)

    def loop(self):
        while True:
            if self.is_enabled():
                if not self.is_setup_complete():
                    self._logger.warning("Invalid URL or Authorisation Token")
                    time.sleep(1)
                    next

                self.is_new_job()
                if self.ws:
                    msg = self.ws_data()
                    self.ws.send_msg(msg)

                if self.len_img_lst < len(self.img_lst):
                    self.len_img_lst = len(self.img_lst)
                    self.set_snapshot_count(self.len_img_lst)
                    latest_img = self.get_latest_img()
                    if latest_img:
                        self.post_img(open(latest_img, "rb"))

            time.sleep(1)

__plugin_name__ = 'Mattacloud'


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = MattacloudPlugin()
    global __plugin_hooks__
    __plugin_hooks__ = {
        'octoprint.plugin.softwareupdate.check_config': __plugin_implementation__.get_update_information
    }

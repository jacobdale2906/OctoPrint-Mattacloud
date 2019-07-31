#!/usr/bin/python
# -*- coding: utf-8 -*-
# coding = utf - 8

from __future__ import absolute_import

import cgi
import datetime
import io
import json
import os
import threading
import time

import flask
import requests
from watchdog.observers import Observer

import octoprint.plugin
from octoprint.filemanager import FileDestinations
from octoprint.filemanager.util import StreamWrapper, DiskFileWrapper

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
        return self._printer.get_current_data()

    def get_current_job(self):
        return self._printer.get_current_job()

    def get_printer_temps(self):
        return self._printer.get_current_temperatures()

    def get_files(self):
        return self._file_manager.list_files(recursive=True)

    # TODO: Improve URL creation
    # Should write a urljoin function
    def get_base_url(self):
        if not self._settings.get(["base_url"]):
            self._logger.warning("No base URL in OctoPrint settings")
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
        url = base_url + "/api"
        return url

    def get_ws_url(self):
        api_url = self.get_api_url()
        url = api_url + "/ws/printer/"
        url = url.replace("http", "ws")
        return url

    def get_ping_url(self):
        api_url = self.get_api_url()
        url = api_url + "/ping/"
        return url

    def get_data_url(self):
        api_url = self.get_api_url()
        url = api_url + "/receive/data/"
        return url

    def get_img_url(self):
        api_url = self.get_api_url()
        url = api_url + "/receive/img/"
        return url

    def get_gcode_url(self):
        api_url = self.get_api_url()
        url = api_url + "/receive/gcode/"
        return url

    def get_request_url(self):
        api_url = self.get_api_url()
        url = api_url + "/receive/request/"
        return url

    def get_auth_token(self):
        if not self._settings.get(["authorization_token"]):
            return None
        return self._settings.get(["authorization_token"])

    def make_auth_header(self, token=None):
        if not token:
            token = self.get_auth_token()
        return {"Authorization": "Token {}".format(token)}

    def on_after_startup(self):
        self._logger.info("Starting OctoPrint-Mattacloud Plugin...")
        self.img_lst = []
        self.len_img_lst = 0
        self.new_print_job = False
        self.ws = None
        dir_path = self.get_octolapse_dir()
        main_thread = threading.Thread(target=self.loop)
        main_thread.daemon = True
        main_thread.start()
        watchdog_thread = threading.Thread(
            target=self.run_observer, args=(dir_path,))
        watchdog_thread.daemon = True
        watchdog_thread.start()
        self.ws_connect()

    def on_event(self, event, payload):
        if self.is_enabled() and hasattr(self, "ws"):
            msg = self.event_ws_data(event, payload)
            self.ws.send_msg(msg)

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

    def get_latest_img(self):
        return self.img_lst[-1]

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
            "config": 1 if self.is_config_print() else 0,
        }
        return data

    def handle_cmds(self, json_msg):
        if "cmd" in json_msg:
            if json_msg["cmd"].lower() == "pause":
                self._printer.pause_print()
            if json_msg["cmd"].lower() == "resume":
                self._printer.resume_print()
            if json_msg["cmd"].lower() == "cancel":
                self._printer.cancel_print()
            if json_msg["cmd"].lower() == "toggle":
                self._printer.toggle_pause_print()
            if json_msg["cmd"].lower() == "print":
                if "file" in json_msg and "loc" in json_msg:
                    file_to_print = json_msg["file"]
                    on_sd = True if json_msg["loc"].lower() == "sd" else False
                    self._printer.select_file(
                        json_msg["file"], sd=on_sd, printAfterSelect=True)
            if json_msg["cmd"].lower() == "select":
                if "file" in json_msg and "loc" in json_msg:
                    file_to_print = json_msg["file"]
                    on_sd = True if json_msg["loc"].lower() == "sd" else False
                    self._printer.select_file(json_msg["file"], sd=on_sd)
            if json_msg["cmd"].lower() == "home":
                if "axes" in json_msg:
                    axes = json_msg["axes"]
                    # TODO: Deal with one or multiple axes
                    self._printer.home(axes=axes)
                else:
                    self._printer.home()
            if json_msg["cmd"].lower() == "jog":
                if "axes" in json_msg:
                    axes = json_msg["axes"]
                    # TODO: Check if axes dict is valid
                    # Axes and distances to jog, keys are axes (“x”, “y”, “z”),
                    # values are distances in mm
                    self._printer.jog(axes=axes, relative=True)
            if json_msg["cmd"].lower() == "extrude":
                if "amt" in json_msg:
                    amt = json_msg["amt"]
                    self._printer.extrude(amount=amt)
            if json_msg["cmd"].lower() == "retract":
                if "amt" in json_msg:
                    amt = -json_msg["amt"]
                    self._printer.extrude(amount=amt)
            if json_msg["cmd"].lower() == "change_tool":
                if "tool" in json_msg:
                    new_tool = "tool{}".format(json_msg["tool"])
                    self._printer.change_tool(tool=new_tool)
            if json_msg["cmd"].lower() == "feed_rate":
                if "factor" in json_msg:
                    new_factor = json_msg["factor"]
                    # TODO: Add checking to see if valid factor
                    # Percentage expressed as either an int between 0 and 100
                    # or a float between 0 and 1.
                    self._printer.feed_rate(factor=new_factor)
            if json_msg["cmd"].lower() == "flow_rate":
                if "factor" in json_msg:
                    new_factor = json_msg["factor"]
                    # TODO: Add checking to see if valid factor
                    # Percentage expressed as either an int between 0 and 100
                    # or a float between 0 and 1.
                    self._printer.flow_rate(factor=new_factor)
            if json_msg["cmd"].lower() == "gcode":
                if "commands" in json_msg:
                    gcode_cmds = json_msg["commands"]
                    # TODO: Check if single (str) or multiple (lst)
                    self._printer.commands(commands=gcode_cmds)
            if json_msg["cmd"].lower() == "temperature":
                if "heater" in json_msg and "val" in json_msg:
                    # TODO: More elegantly handle different inputs
                    # e.g. bed, tool0, tool1, 0, 1
                    heater = json_msg["heater"]
                    if heater != "bed":
                        heater = "tool{}".format(heater)
                    val = json_msg["val"]
                    self._printer.set_temperature(heater=heater, value=val)
            if json_msg["cmd"].lower() == "temperature_offset":
                if "offsets" in json_msg:
                    # TODO: Validate the "offsets" dict
                    # Keys must match the format for the heater parameter
                    # to set_temperature(), so “bed” for the offset for the
                    # bed target temperature and “tool[0-9]+” for the
                    # offsets to the hotend target temperatures.
                    offsets = json_msg["offsets"]
                    self._printer.set_temperature_offset(offset=offsets)
            if json_msg["cmd"].lower() == "upload_request":
                # TODO: Add loc to server side
                self._logger.info("upload_request")
                self._logger.info(json_msg)
                if "id" in json_msg and "loc" in json_msg:
                    if json_msg["loc"].lower() == "sd":
                        location = FileDestinations.SDCARD
                    elif json_msg["loc"].lower() == "local":
                        location = FileDestinations.LOCAL
                    else:
                        # TODO: Handle this error
                        location = FileDestinations.LOCAL
                        self._logger.error("Invalid file destination")
                    path = self.post_upload_request(file_id=json_msg["id"])
                    self._logger.info(path)
                    self._logger.info(self._file_manager._printer_profile_manager.get_default())
                    self._logger.info(self._file_manager._printer_profile_manager)
                    # result = self._file_manager.analyse(destination=location, path=path)
                    # self._logger.info(result)
                    # TODO: Handle analysis for SD card files
                    is_analysed = self._file_manager.has_analysis(destination=location,
                                                                  path=path)
                    self._logger.info(is_analysed)
                    if not is_analysed:
                        pass
            if json_msg["cmd"].lower() == "new_folder":
                if "folder" in json_msg and "loc" in json_msg:
                    folder_name = json_msg["folder"]
                    if json_msg["loc"].lower() == "sd":
                        location = FileDestinations.SDCARD
                    elif json_msg["loc"].lower() == "local":
                        location = FileDestinations.LOCAL
                    else:
                        # TODO: Handle this error
                        location = FileDestinations.LOCAL
                        self._logger.error("Invalid file destination")
                    # TODO: Destination both local and SD card.
                    self._file_manager.add_folder(destination=location,
                                                  path=folder_name,
                                                  ignore_existing=True,
                                                  display=None)
            if json_msg["cmd"].lower() == "delete":
                if "file" in json_msg and "loc" in json_msg and "type" in json_msg:
                    file_to_delete = json_msg["file"]
                    if json_msg["loc"].lower() == "sd":
                        location = FileDestinations.SDCARD
                    elif json_msg["loc"].lower() == "local":
                        location = FileDestinations.LOCAL
                    else:
                        # TODO: Handle this error
                        location = FileDestinations.LOCAL
                        self._logger.error("Invalid file destination")
                    if json_msg["type"] == "file":
                        self._file_manager.remove_file(destination=location,
                                                       path=file_to_delete)
                    elif json_msg["type"] == "folder":
                        self._file_manager.remove_folder(destination=location,
                                                         path=file_to_delete)
                    else:
                        self._logger.error("Incorrect type {} provided".format(json_msg["type"]))

    def process_response(self, resp):
        # TODO: Handle different types of response
        content_disposition = resp.headers["Content-Disposition"]
        value, params = cgi.parse_header(content_disposition)
        filename = params["filename"]
        file_content = resp.text.replace("\\n", "\n")
        stream = io.StringIO(file_content, newline="\n")
        stream_wrapper = StreamWrapper(filename, stream)

        try:
            future_path, future_filename = self._file_manager.sanitize(FileDestinations.LOCAL, filename)
        except:
            future_path = None
            future_filename = None
        future_full_path = self._file_manager.join_path(FileDestinations.LOCAL, future_path, future_filename)
        future_full_path_in_storage = self._file_manager.path_in_storage(FileDestinations.LOCAL, future_full_path)

        if not self._printer.can_modify_file(future_full_path_in_storage, False):
            return

        reselect = self._printer.is_current_file(future_full_path_in_storage, False)
        # Destination both local and SD card.
        path = self._file_manager.add_file(destination=FileDestinations.LOCAL,
                                           path=filename,
                                           file_object=stream_wrapper,
                                           allow_overwrite=True)
        if os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass

        if reselect:
            self._printer.select_file(self._file_manager.path_on_disk(FileDestinations.LOCAL,
                                                                      added_file),
                                      False)
        return path

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
            if os.path.exists(path):
                try:
                    with open(path, "rb") as gcode:
                        url = self.get_gcode_url()

                        files = {
                            "gcode": gcode,
                        }

                        resp = requests.post(
                            url=url,
                            files=files,
                            data=data,
                            headers=self.make_auth_header()
                        )
                        resp.raise_for_status()

                except (OSError, IOError) as e:
                    self._logger.error("Failed to open gcode file: {}".format(path))
            else:
                self._logger.error("Gcode file does not exist: {}".format(path))

    def post_img(self, img=None):
        self._logger.info("Posting image")
        if not self.is_setup_complete():
            self._logger.warning("Printer not ready")
            return

        url = self.get_img_url()

        if not img:
            pass

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
            headers=self.make_auth_header()
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
            headers=self.make_auth_header()
        )
        resp.raise_for_status()
        self.process_response(resp)

    def post_upload_request(self, file_id):
        self._logger.info("Posting upload request")
        if not self.is_setup_complete():
            self._logger.warning("Printer not ready")
            return

        data = {
            "timestamp": self.make_timestamp(),
            "status": "ready",
            "type": "file",
            "file_id": file_id,
        }

        url = self.get_request_url()

        resp = requests.post(
            url=url,
            json=data,
            headers=self.make_auth_header()
        )
        resp.raise_for_status()
        path = self.process_response(resp)

        data = {
            "timestamp": self.make_timestamp(),
            "status": "success",
            "type": "file",
            "file_id": file_id,
        }

        resp = requests.post(
            url=url,
            json=data,
            headers=self.make_auth_header()
        )
        resp.raise_for_status()
        return path

    def get_api_commands(self):
        return dict(
            test_auth_token=["auth_token"],
            set_enabled=[],
            set_config_print=[],
        )

    def is_api_adminonly(self):
        return True

    def on_api_command(self, command, data):
        if command == "test_auth_token":
            auth_token = data["auth_token"]
            success, status_text = self.test_auth_token(token=auth_token)
            if success:
                self._settings.set(["authorization_token"],
                                   auth_token, force=True)
                self._settings.save(force=True)
            return flask.jsonify({"success": success, "text": status_text})
        if command == "set_enabled":
            previous_enabled = self._settings.get(["enabled"])
            self._settings.set(["enabled"], not previous_enabled, force=True)
            self._settings.save(force=True)
            is_enabled = self._settings.get(["enabled"])
            return flask.jsonify({"success": True, "enabled": is_enabled})
        if command == "set_config_print":
            previous_config_print = self._settings.get(["config_print"])
            self._settings.set(
                ["config_print"], not previous_config_print, force=True)
            self._settings.save(force=True)
            is_config_print = not previous_config_print
            return flask.jsonify({"success": True, "config_print_enabled": is_config_print})

    def test_auth_token(self, token):
        url = self.get_ping_url()
        success = False
        status_text = "Oh no! An unknown error occurred."
        try:
            resp = requests.get(
                url=url,
                headers=self.make_auth_header(token=token)
            )
            success = resp.ok
            if resp.status_code == 200:
                status_text = "All is tickety boo! Your token is valid."
            elif resp.status_code == 401:
                status_text = "Whoopsie. That token is invalid."
            else:
                status_text = "Oh no! An unknown error occurred."
        except:
            # TODO: Catch the correct exceptions
            status_text = "Connection error. Please check OctoPrint\'s internet connection"
        return success, status_text

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
                    self._logger.debug("Websocketing")
                    msg = self.ws_data()
                    self.ws.send_msg(msg)

                if self.len_img_lst < len(self.img_lst):
                    self.len_img_lst = len(self.img_lst)
                    self.set_snapshot_count(self.len_img_lst)
                    latest_img = self.get_latest_img()
                    if latest_img:
                        self.post_img(open(latest_img, "rb"))

            time.sleep(1)

__plugin_name__ = "Mattacloud"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = MattacloudPlugin()
    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }

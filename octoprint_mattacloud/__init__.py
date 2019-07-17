#!/usr/bin/python
# -*- coding: utf-8 -*-
# coding = utf - 8

from __future__ import absolute_import

import octoprint.plugin

import logging

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
        pass

    def get_ws_url(self):
        pass

    def get_ping_url(self):
        pass

    def get_data_url(self):
        pass

    def get_img_url(self):
        pass

    def get_gcode_url(self):
        pass

    def get_request_url(self):
        pass

    def get_auth_token(self):
        if not self._settings.get(["authorization_token"]):
            return None
        return self._settings.get(["authorization_token"])

    def on_after_startup(self):
        self._logger.info("Starting OctoPrint-Mattacloud Plugin...")

    def on_event(self, event, payload):
        self._logger.info("Event: " + str(event))
        self._logger.info("Payload: " + str(payload))

    def is_enabled(self):
        return self._settings.get(["enabled"])

    def is_operational(self):
        return self._printer.is_ready() or self._printer.is_operational()

    def is_setup_complete(self):
        return self.get_base_url() and self.get_auth_token()


__plugin_name__ = 'Mattacloud'


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = MattacloudPlugin()
    global __plugin_hooks__
    __plugin_hooks__ = {
        'octoprint.plugin.softwareupdate.check_config': __plugin_implementation__.get_update_information
    }

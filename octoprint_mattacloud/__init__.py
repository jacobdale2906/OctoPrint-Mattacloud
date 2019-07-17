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
        return dict()

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

    def on_after_startup(self):
        self._logger.info("Starting OctoPrint-Mattacloud Plugin...")


__plugin_name__ = 'Mattacloud'


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = MattacloudPlugin()
    global __plugin_hooks__
    __plugin_hooks__ = {
        'octoprint.plugin.softwareupdate.check_config': __plugin_implementation__.get_update_information
    }

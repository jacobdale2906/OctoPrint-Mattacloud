$(function () {

    // This is for the settings page
    var settings_test_btn = document.getElementById("settings_test_btn");
    settings_test_btn.onclick = function () {
        console.log("Settings Test Auth Token Button");
        var settings_test_btn_spin = document.getElementById("settings_test_btn_spin");
        settings_test_btn_spin.style.display = "inline-block";
        settings_test_token();
    };

    settings_test_token = function () {
        var data = {
            command: "test_auth_token",
            auth_token: document.getElementById("settings_token_input").value,
            url: document.getElementById("settings_url_input").value,
        };
        console.log(data);
        $.ajax({
            url: "./api/plugin/mattacloud",
            type: "POST",
            data: JSON.stringify(data),
            contentType: "application/json",
            dataType: "json",
            success: function (status) {
                if (status.success) {
                    new PNotify({
                        title: gettext("Connection"),
                        text: gettext(status.text),
                        type: "success"
                    });
                } else {
                    new PNotify({
                        title: gettext("Connection"),
                        text: gettext(status.text),
                        type: "error"
                    });
                }
                settings_test_btn_spin.style.display = "none";
            },
        });
    }

    function MattacloudViewModel(parameters) {
        var self = this;

        self.loginState = parameters[0];
        self.settings = parameters[1];

        self.auth_token = ko.observable();
        self.server_address = ko.observable();
        self.snapshot_dir = ko.observable();
        self.upload_dir = ko.observable();
        self.enabled_value = ko.observable();
        self.snapshot_count_value = ko.observable();
        self.config_print = ko.observable();
        self.ws_connected = ko.observable();

        self.snapshot_url_1 = ko.observable();
        self.snapshot_url_2 = ko.observable();

        self.temperature_interval = ko.observable();
        self.vibration_interval = ko.observable();
        self.camera_1_interval = ko.observable();
        self.camera_2_interval = ko.observable();

        self.is_octoprint_admin = ko.observable(self.loginState.isAdmin());

        self.ws_status = ko.observable();
    
        var ws_reconnect_btn = document.getElementById("ws_reconnect_btn");
        ws_reconnect_btn.onclick = function () {
            var ws_reconnect_btn_spin = document.getElementById("ws_reconnect_btn_spin");
            ws_reconnect_btn_spin.style.display = "inline-block";
            ws_reconnect();
        };
    
        ws_reconnect = function () {
            var data = {
                command: "ws_reconnect",
            };
            $.ajax({
                url: "./api/plugin/mattacloud",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (result) {
                    var status = 'Disconnected.';
                    if (result.success) {
                        status = 'Connected to the mattacloud.';
                        new PNotify({
                            title: gettext("Connection"),
                            text: gettext(result.text),
                            type: "success"
                        });
                    } else {
                        new PNotify({
                            title: gettext("Connection"),
                            text: gettext(result.text),
                            type: "error"
                        });
                    }
                    ws_reconnect_btn_spin.style.display = "none";
                    
                    self.ws_status(status);
                },
            });
        }

        self.enabled = ko.pureComputed(function () {
            if (self.enabled_value()) {
                if (self.config_print()) {
                    return 'Mattacloud - Running (Config Print)';
                }
                return 'Mattacloud - Running';
            }
            return 'Mattacloud - Disabled';
        }, self);

        go_to_settings = function () {
            $('#navbar_show_settings').trigger( "click" );
            $('#settings_plugin_mattacloud_link a').trigger( "click" );
        }

        self.status = ko.pureComputed(function () {
            if (self.enabled_value()) {
                if (self.config_print()) {
                    return 'Mattacloud is enabled, idle and set to run a configuration print.';
                }
                return 'Mattacloud is enabled and idle.';
            }
            return 'Mattacloud is disabled.';
        }, self);

        self.toggle_mattacloud = function () {
            var data = {
                command: "set_enabled",
            };
            console.log("Toggling mattacloud.")
            $.ajax({
                url: "./api/plugin/mattacloud",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (status) {
                    console.log("Enabled " + status.enabled);
                    self.enabled_value(status.enabled);
                },
            });
            return true;
        };

        self.set_config_print = function () {
            console.log("Config Print");
            var data = {
                command: "set_config_print",
            };
            $.ajax({
                url: "./api/plugin/mattacloud",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (status) {
                    console.log("Config " + status.config_print_enabled);
                    self.config_print(status.config_print_enabled);
                },
            });
            return true;
        };

        update_status_text = function () {
            var status_text = "Disconnected.";
            if (self.ws_connected()) {
                status_text = "Connected to the mattacloud.";
            }
            self.ws_status(status_text);
        }

        self.onBeforeBinding = function () {
            self.auth_token(self.settings.settings.plugins.mattacloud.authorization_token());
            self.server_address(self.settings.settings.plugins.mattacloud.base_url());
            self.snapshot_dir(self.settings.settings.plugins.mattacloud.snapshot_dir());
            self.snapshot_count_value(self.settings.settings.plugins.mattacloud.snapshot_count());
            self.upload_dir(self.settings.settings.plugins.mattacloud.upload_dir());
            self.config_print(self.settings.settings.plugins.mattacloud.config_print());
            self.enabled_value(self.settings.settings.plugins.mattacloud.enabled());
            self.ws_connected(self.settings.settings.plugins.mattacloud.ws_connected());
            self.temperature_interval(self.settings.settings.plugins.mattacloud.temperature_interval());
            self.vibration_interval(self.settings.settings.plugins.mattacloud.vibration_interval());
            self.camera_1_interval(self.settings.settings.plugins.mattacloud.camera_interval_1());
            self.camera_2_interval(self.settings.settings.plugins.mattacloud.camera_interval_2());
            self.snapshot_url_1(self.settings.settings.plugins.mattacloud.snapshot_url_1());
            self.snapshot_url_2(self.settings.settings.plugins.mattacloud.snapshot_url_2());
            update_status_text();
        }
    }

    // This is how our plugin registers itself with the application, by adding some configuration
    // information to the global variable OCTOPRINT_VIEWMODELS
    OCTOPRINT_VIEWMODELS.push([
        MattacloudViewModel,
        ["loginStateViewModel", "settingsViewModel"],
        ["#settings_plugin_mattacloud", "#tab_plugin_mattacloud"]
    ]);
});
$(function () {

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

        self.ws_status = ko.observable();

        var test_auth_token_btn = document.getElementById("test_auth_token_btn");
        test_auth_token_btn.onclick = function () {
            var test_auth_token_btn_spin = document.getElementById("test_auth_token_btn_spin");
            test_auth_token_btn_spin.style.display = "inline-block";
            test_auth_token();
        };
    
        test_auth_token = function () {
            var data = {
                command: "test_auth_token",
                auth_token: document.getElementById("auth_token_input").value,
            };
            $.ajax({
                url: "./api/plugin/mattacloud",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (status) {
                    var token_test_response = document.getElementById("token_test_response");
                    token_test_response.classList.remove("text-error");
                    token_test_response.classList.remove("text-success");
                    if (status.success) {
                        token_test_response.classList.add("text-success");
                    } else {
                        token_test_response.classList.add("text-error");
                    }
                    token_test_response.innerHTML = status.text;
                    test_auth_token_btn_spin.style.display = "none";
                },
            });
        }
    
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
                    var token_test_response = document.getElementById("ws_reconnect_response");
                    token_test_response.classList.remove("text-error");
                    token_test_response.classList.remove("text-success");
                    var status = 'Status: Disconnected.';
                    if (result.success) {
                        token_test_response.classList.add("text-success");
                        status = 'Status: Connected to the mattacloud.';
                    } else {
                        token_test_response.classList.add("text-error");
                    }
                    token_test_response.innerHTML = result.text;
                    ws_reconnect_btn_spin.style.display = "none";
                    self.ws_connected(result.success);
                    
                    self.ws_status(status);
                    console.log(self.ws_connected());
                    console.log(self.ws_status());
                    console.log(self.settings.settings.plugins.mattacloud.ws_connected());
                },
            });
        }

        self.enabled = ko.pureComputed(function () {
            if (self.enabled_value()) {
                if (self.config_print()) {
                    return 'Mattacloud Plugin - Running (Configuration Print)';
                }
                return 'Mattacloud Plugin - Running';
            }
            return 'Mattacloud Plugin - Disabled';
        }, self);

        self.status = ko.pureComputed(function () {
            if (self.enabled_value()) {
                if (self.config_print()) {
                    return 'Status: Mattacloud is enabled, idle and set to run a configuration print.';
                }
                return 'Status: Mattacloud is enabled and idle.';
            }
            return 'Status: Mattacloud is disabled.';
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
                    console.log("Enabled status: " + status.enabled);
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
                    console.log("Config status: " + status.config_print_enabled);
                    self.config_print(status.config_print_enabled);
                },
            });
            return true;
        };

        // This will get called before the HelloWorldViewModel gets bound to the DOM, but after its
        // dependencies have already been initialized. It is especially guaranteed that this method
        // gets called _after_ the settings have been retrieved from the OctoPrint backend and thus
        // the SettingsViewModel been properly populated.
        self.onBeforeBinding = function () {
            self.auth_token(self.settings.settings.plugins.mattacloud.authorization_token());
            self.server_address(self.settings.settings.plugins.mattacloud.base_url());
            self.snapshot_dir(self.settings.settings.plugins.mattacloud.snapshot_dir());
            self.snapshot_count_value(self.settings.settings.plugins.mattacloud.snapshot_count());
            self.upload_dir(self.settings.settings.plugins.mattacloud.upload_dir());
            self.config_print(self.settings.settings.plugins.mattacloud.config_print());
            self.enabled_value(self.settings.settings.plugins.mattacloud.enabled());
            self.ws_connected(self.settings.settings.plugins.mattacloud.ws_connected());
        }
    }

    // This is how our plugin registers itself with the application, by adding some configuration
    // information to the global variable OCTOPRINT_VIEWMODELS
    OCTOPRINT_VIEWMODELS.push([
        // This is the constructor to call for instantiating the plugin
        MattacloudViewModel,

        // This is a list of dependencies to inject into the plugin, the order which you request
        // here is the order in which the dependencies will be injected into your view model upon
        // instantiation via the parameters argument
        ["loginStateViewModel", "settingsViewModel"],

        // Finally, this is the list of selectors for all elements we want this view model to be bound to.
        ["#tab_plugin_mattacloud", "#tab_plugin_mattalcoud_panel_heading", "#tab_plugin_mattalcoud_panel_body"]
    ]);
});
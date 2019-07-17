$(function () {

    $("#test_auth_token_btn").click(function (event) {
        $('#test_auth_token_btn_spin').show();
        test_auth_token();
    });

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
                $('#test_auth_token_btn_spin').hide();
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

        self.enabled = ko.pureComputed(function () {
            if (self.enabled_value()) {
                if (self.config_print()) {
                    return 'Mattacloud - Running Configuration';
                }
                return 'Mattacloud - Running';
            }
            return 'Mattacloud - Disabled';
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

        self.snapshot_count = function () {
            console.log("Snapshot count");
        };

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
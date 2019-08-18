# OctoPrint-Mattacloud

Automatic and intelligent error detection and process monitoring for your OctoPrint enabled 3D printer with full remote control and management from anywhere. Additionally, receive notifications and updates via your chosen communications medium, alerting you of failures and updating you on your 3D print.

### Error detection and process monitoring

3D printers are not the most reliable of machines. All of us have suffered from errors whilst printing and many users feel _handcuffed_ to their printers, having to constantly check every 5 minutes to make sure that the print is _still_ okay! If this sounds familiar... hopefully this plugin will help.

Numerous computer vision techniques are used to determine if an error has occurred during your 3D print. Using a mixture of machine learning, 3D printing heuristics and the direct comparison of g-code to the current state of the 3D print, an error can be reliably determined in an image of the 3D print.

Errors that are currently detected reliably:

- Detatchment from print bed
- Offset
- Warping
- Poor bed adhesion
- Spaghetti
- Blocked extruder / out of filament
- Hotend too close to print bed

### Remote control and management

Access your 3D printer from anywhere in the world (provided that there is an internet connection...) via the OctoPrint-Mattacloud Plugin.

At present, the plugin enables you to do the following:

- View and update hotend, bed and chamber temperatures
- Control and home X, Y and Z axes
- Select prints to retrieve information
- Start, cancel, pause, resume and restart 3D prints
- Upload g-code files remotely to your printer for printing
- Delete g-code files remotely
- Receive the latest images/snapshots from your printer
- See your prints progress (time remaining and percentage completion)

### Notifications and updates

By installing this plugin and linking your printer to a mattacloud account you can receive useful notifications and updates concerning your 3D printer via various channels. When an error occurs during the 3D printing process, you will receive an alert with an attached image showing the error in addition to current progress, material used and other useful stats. You can then deside to take action. You can also set up other checkpoints to receive notifications, such as upon object completion, or when a print has reached the half way mark. 

The communication channels which are currently supported are:

- Email
- SMS (Beta)
- WhatsApp (Beta)
- Facebook Messenger (Beta)

## Setup

Install via the bundled [OctoPrint Plugin Manager](https://github.com/foosel/OctoPrint/wiki/Plugin:-Plugin-Manager)
or manually using this URL:

    https://github.com/dougbrion/OctoPrint-Mattacloud/archive/master.zip

After downloading the zip file of the latest release, install it using the OctoPrint Plugin Manager.

## Setup

**TODO:** Describe the plugin's configuration options.

## Report problems

If something does not appear to be working correctly and you think you may have found a bug in the OctoPrint-Mattacloud plugin, please create an issue on the official page [here](https://github.com/dougbrion/OctoPrint-Mattacloud/issues). In this way your issue can be understood and fixed quickly.

## Data

## License

View the [OctoPrint-Mattacloud plugin license](https://github.com/dougbrion/OctoPrint-Mattacloud/blob/master/LICENSE)

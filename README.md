# Setup

CommuniApi class requires params for your Communi configuration.

## Initial configuration
This package requires the ChurchToolsApi to be installed.
If you setup this package using pip it should be a required dependency.
If you only downloaded this code without package management you will need to install it to your python environment

Check https://github.com/bensteUEM/ChurchToolsAPI/releases for the latest realease.

### How to use with config.py
By default some changes need to be made to config.py before first use.
(if you want to use it as config params)

1 Get your REST access token from your instance
e.g. https://YOURINSTANCE.communiapp.de/page/integration/tab/rest
and save it in the configuration file.
```
token = 'ENTER-YOUR-TOKEN-HERE'
```
All requests are executed against the central REST server of communi which is part of the default config
This part does likely not need any change unless you have a special configuration.
```
rest_server = 'https://api.communiapp.de/rest'
```
In order to addres your own instance (matching to the token) you need to change the communiApp in the config
Please note that the AppID is NOT the same as the primary group ID. As this is undocumented please consult with Communi to retrieve your ID or reverse engineer using a web-client.
```
communiApp = 0
```

In addition the login details for a ChurchTools instance is required for CT specific access
```
ct_domain = 'https://XXX'
ct_token = ###
```

ct_users = {'username': 'test'}

# Usage

The script is maintained using VS Studio Code.
Test cases are run against my own instance - please adapt to yours before changing any code and make sure they run successfully!
Be aware that some of the test cases require specific IDs to be present on your instance.
The respective function do have a hint like the one below in the docstring of the respective functions
```
IMPORTANT - This test method and the parameters used depend on the target system!
```

## Compatibility

Tested against the current CommuniAPIs as of July 2023.
More information is provided on the respective Communi pages.

# License

This code is provided with a CC-BY-SA license
See https://creativecommons.org/licenses/by-sa/2.0/ for details.

In short this means - feel free to do anything with it
BUT you are required to publish any changes or additional functionality (even if you intended to add functionality for
yourself only!)

Anybody using this code is more than welcome to contribute with change requests to the original repository.

## Contributors 
benste - implemented for use at Evangelische Kirchengemeinde Baiersbronn (https://www.evang-kirche-baiersbronn.de/)
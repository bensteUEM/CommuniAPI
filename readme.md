# Setup

This code requires a config.py within the "secure" folder in order to work

## Initial configuration

### Server connection
Some changes need to be made to defaults.py before first use.

1 Get your REST access token from your instance
e.g. https://YOURINSTANCE.communiapp.de/page/integration/tab/rest
and save it in the configuration file.

```
token = 'ENTER-YOUR-TOKEN-HERE'
```

All requests are executed against the central REST server of communi which is part of the default config
This part does likely not need any change unless you have a special configuration.
```
rest_server = 'api.communiapp.de/rest/'
```

In order to addres your own instance (matching to the token) you need to change the communiApp in the config
```
communiApp = 0
```

# Usage

The script was coded using PyCharm Community edition. It is highly recomended to run the test cases successfully before use.
Please be aware that some of the test cases require specific IDs to be present on your instance.
The respective function do have a hint like the one below in the docstring of the respective functions
```
IMPORTANT - This test method and the parameters used depend on the target system!
```

## Compatibility

Tested against the current CommuniAPIs as of January 2023.
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
import logging
import unittest

from CommuniApi import CommuniApi


class TestsCommuniApp(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestsCommuniApp, self).__init__(*args, **kwargs)
        self.api = CommuniApi()
        logging.basicConfig(filename='logs/TestsCommuniApp.log', encoding='utf-8',
                            format="%(asctime)s %(name)-10s %(levelname)-8s %(message)s",
                            level=logging.DEBUG)
        logging.info("Executing Tests RUN")

    def test_config(self):
        self.assertNotEqual(self.api.communiAppId, 0, 'Please configure a propper App ID in config.py')
        self.assertNotEqual(self.api.token, 'ENTER-YOUR-TOKEN-HERE', 'Please change the default token in config.py')
        self.assertEqual(self.api.rest_server, 'api.communiapp.de/rest/', 'Are you sure your server is correct?')

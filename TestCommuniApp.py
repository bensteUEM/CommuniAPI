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
        self.assertEqual(self.api.rest_server, 'https://api.communiapp.de/rest', 'Are you sure your server is correct?')

    def test_login(self):
        result = self.api.login()
        self.assertTrue(result)

    def test_getUserList(self):
        result = self.api.getUserList()
        self.assertGreater(len(result), 0)

    def test_createGroup(self):
        result = self.api.createGroup(title="_TesCommuniApp",
                                      description="Group used by Python Test Case for Automation",
                                      access_type_open=False, hasGroupChat=True)
        self.assertTrue(result)

    def test_getGroups(self):
        """
        IMPORTANT - This test method and the parameters used depend on the target system!
        :return:
        """
        result = self.api.getGroups()
        self.assertGreater(len(result), 0)

        result = self.api.getGroups(id=7525)['title']
        test_title = 'Evang. Kirche Baiersbronn'
        self.assertEqual(result, test_title)

        result = self.api.getGroups(name='Jungenschaft')['id']
        test_id = 7646
        self.assertEqual(result, test_id)

    def test_deleteGroup(self):
        """
        Test that creates two new groups and deletes them one by id and one by name
        IMPORTANT - This test method and the parameters used depend on the target system!
        :return:
        """
        description = 'created by test_deleteGroup() function should be auto deleted after successful test\n' \
                      'feel free to delete this group manually if it still exists'
        group1 = self.api.createGroup("Test1", description)
        group2 = self.api.createGroup("Test2", description)
        group2 = self.api.getGroups(id=group2['id'])

        result = self.api.deleteGroup(id=group1['id'])
        self.assertTrue(result)

        result2 = self.api.deleteGroup(name=group2['title'])
        self.assertTrue(result)

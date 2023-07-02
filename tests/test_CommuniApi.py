import logging
import os
import unittest
from datetime import datetime

from ChurchToolsApi import ChurchToolsApi
from CommuniApi import CommuniApi
from CommuniApi.churchToolsActions import create_event_chats, delete_event_chats

class TestsCommuniApp(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestsCommuniApp, self).__init__(*args, **kwargs)
        os.makedirs('logs', exist_ok=True)
        logging.basicConfig(filename='logs/TestsCommuniApp.log', encoding='utf-8',
                            format="%(asctime)s %(name)-10s %(levelname)-8s %(message)s",
                            level=logging.DEBUG)
        
        if 'COMMUNI_TOKEN' in os.environ:
            self.COMMUNI_TOKEN = os.environ['COMMUNI_TOKEN']
            self.COMMUNI_SERVER = os.environ['COMMUNI_SERVER']
            self.COMMUNI_APPID = os.environ['COMMUNI_APPID']
            self.CT_TOKEN =  os.environ['CT_TOKEN']
            self.CT_DOMAIN =  os.environ['CT_DOMAIN']
            logging.info('using connection details provided with ENV variables')
        else:
            from secure.config import token, rest_server, communiAppId
            self.COMMUNI_TOKEN = token
            self.COMMUNI_SERVER = rest_server
            self.COMMUNI_APPID = communiAppId
            from secure.config import ct_token, ct_domain
            self.CT_TOKEN = ct_token
            self.CT_DOMAIN =  ct_domain
            logging.info('using connection details provided from secrets folder')

        self.api = CommuniApi(self.COMMUNI_SERVER, self.COMMUNI_TOKEN, self.COMMUNI_APPID)
        self.ct_api = ChurchToolsApi(self.CT_DOMAIN, self.CT_TOKEN)
        logging.info("Executing Tests RUN")

    def tearDown(self):
        """
        Destroy the session after test execution to avoid resource issues
        :return:
        """
        self.api.session.close()

    def test_config(self):
        self.assertNotEqual(self.api.communi_appid, 0, 'Please configure a propper App ID in config.py')
        self.assertNotEqual(self.api.communi_token, 'ENTER-YOUR-TOKEN-HERE', 'Please change the default token in config.py')
        self.assertEqual(self.api.communi_server, 'https://api.communiapp.de/rest', 'Are you sure your server is correct?')

    def test_login(self):
        if self.api.session is not None:
            self.api.session.close()
        result = self.api.login()
        self.assertTrue(result)

    def test_login_wrong_app(self):
        temp_COMMUNI_APPID = self.api.communi_appid
        self.api.communi_appid = 9999
        if self.api.session is not None:
            self.api.session.close()
        result = self.api.login()
        self.assertFalse(result)

        self.api.communi_appid = temp_COMMUNI_APPID
        if self.api.session is not None:
            self.api.session.close()
        result = self.api.login()
        self.assertTrue(result)

    def test_who_am_i(self):
        """
        This test tries to login with invalid credentials
        it will reset to original credentials afterwards
        """

        #Make auth fail on purpose
        old_token = self.api.communi_token
        self.api.communi_token = 'FAIL'

        self.api.login()
        result = self.api.who_am_i()
        self.assertFalse(result)

        self.api.communi_token = old_token
        self.api.login()

        result = self.api.who_am_i()
        self.assertIsInstance(result, dict)
        self.assertIn('id', result.keys())
        self.assertGreaterEqual(result['id'],0)
        self.assertGreaterEqual(len(result['vorname']),1)
        self.assertGreaterEqual(len(result['nachname']),1)
        self.assertIn('mailadresse', result.keys())
        self.assertGreaterEqual(len(result['mailadresse']),1)


    def test_getUserList(self):
        """
        IMPORTANT - This test method and the parameters used depend on the target system!
        userId = 28057 => Admin
        :return:
        """
        userId = 28057

        result = self.api.getUserList()
        self.assertGreater(len(result), 0)

        result = self.api.getUserList(userId=userId)
        self.assertIn('id', result.keys())

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

    def test_createDeleteGroup(self):
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
        self.assertTrue(result2)

    def test_userGroupList(self):
        """
        IMPORTANT - This test method and the parameters used depend on the target system!
        :return:
        """
        user_id = 28057
        group_id = self.api.createGroup("_test_userGroupList ", 'If this group exists some test failed - please delete')['id']
        self.api.changeUserGroup(userId=user_id, groupId=group_id, add_user=True)

        result = self.api.getUserGroupList()
        self.assertGreater(len(result), 0)

        result = self.api.getUserGroupList(user=user_id)
        self.assertGreater(len(result), 1)

        result = self.api.getUserGroupList(group=group_id)
        self.assertGreater(len(result), 1)

        result = self.api.getUserGroupList(group=group_id, user=user_id)
        self.assertEqual(1, len(result))
        self.assertEqual(result[0]['user'], user_id)
        self.assertEqual(result[0]['group'], group_id)

        result = self.api.deleteGroup(id=group_id)
        self.assertTrue(result)

    def test_changeUserGroup(self):
        """
        Tries to add and remove a user from a test group
        IMPORTANT - This test method and the parameters used depend on the target system!
        Testing with userID 28057 (admin)  and groupID 21037 (_TEST Gruppe - UserAdd)
        :return:
        """
        user_id = 28057
        group_id= self.api.createGroup("_test_changeUserGroup ", 'If this group exists some test failed - please delete')['id']

        self.assertFalse(self.api.changeUserGroup(0, 0, False))
        self.assertTrue(self.api.changeUserGroup(user_id, group_id, True))

        test_result = self.api.getUserGroupList(user=user_id, group=group_id)
        self.assertEqual(len(test_result), 1)
        self.assertEqual(test_result[0]['status'], 2)

        self.assertFalse(self.api.changeUserGroup(0, 0, False))
        self.assertTrue(self.api.changeUserGroup(user_id, group_id, False))
        test_result = self.api.getUserGroupList(user=user_id, group=group_id)
        self.assertEqual(test_result[0]['status'], 4)

        result = self.api.deleteGroup(id=group_id)
        self.assertTrue(result)


    def test_message(self):
        """
        Attempts to post a chat message text into a test group
        IMPORTANT - This test method and the parameters used depend on the target system!
        groupID 21037 (_TEST Gruppe - UserAdd)
        :return:
        """
        group_id= self.api.createGroup("_test_message ", 'If this group exists some test failed - please delete')['id']

        timestamp = datetime.now()
        result = self.api.message(groupId=group_id,
                                  text="Hello World from test_postInGroup - on {}".format(timestamp))
        self.assertTrue(result)

        result = self.api.deleteGroup(id=group_id)
        self.assertTrue(result)

    def test_create_event_chats(self):
        """
        Testing method to check if event creation and user update works
        IMPORTANT - This test method and the parameters used depend on the target system!
        event ID 2626 on elkw1610.krz.tools represents a rest event with multiple services
        :return:
        """
        test_event_ids = [2626]
        result = create_event_chats(self.ct_api, self.api, test_event_ids, only_relevant=True)
        self.assertEqual(True, result)

        result = delete_event_chats(self.ct_api, self.api, test_event_ids)
        self.assertEqual(True, result)

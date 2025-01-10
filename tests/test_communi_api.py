import json
import logging
import logging.config
import os
import unittest
from datetime import datetime
from pathlib import Path

from churchtools_api.churchtools_api import ChurchToolsApi

from communi_api.churchToolsActions import create_event_chats, delete_event_chats
from communi_api.communi_api import CommuniApi

logger = logging.getLogger(__name__)

config_file = Path("logging_config.json")
with config_file.open(encoding="utf-8") as f_in:
    logging_config = json.load(f_in)
    log_directory = Path(logging_config["handlers"]["file"]["filename"]).parent
    if not log_directory.exists():
        log_directory.mkdir(parents=True)
    logging.config.dictConfig(config=logging_config)


class TestsCommuniApp(unittest.TestCase):
    def setup_class(self) -> None:
        if "COMMUNI_TOKEN" in os.environ:
            self.COMMUNI_TOKEN = os.environ["COMMUNI_TOKEN"]
            self.COMMUNI_SERVER = os.environ["COMMUNI_SERVER"]
            self.COMMUNI_APPID = os.environ["COMMUNI_APPID"]
            self.CT_TOKEN = os.environ["CT_TOKEN"]
            self.CT_DOMAIN = os.environ["CT_DOMAIN"]
            logger.info("using connection details provided with ENV variables")
        else:
            from secure.config import communiAppId, rest_server, token

            self.COMMUNI_TOKEN = token
            self.COMMUNI_SERVER = rest_server
            self.COMMUNI_APPID = communiAppId
            from secure.config import ct_domain, ct_token

            self.CT_TOKEN = ct_token
            self.CT_DOMAIN = ct_domain
            logger.info("using connection details provided from secrets folder")

        self.api = CommuniApi(
            self.COMMUNI_SERVER, self.COMMUNI_TOKEN, self.COMMUNI_APPID
        )
        self.ct_api = ChurchToolsApi(self.CT_DOMAIN, self.CT_TOKEN)
        logger.info("Executing Tests RUN")

    def tearDown(self) -> None:
        """Destroy the session after test execution to avoid resource issues."""
        self.api.session.close()

    def test_config(self) -> None:
        """Check that configuration exists."""
        assert self.api.communi_appid != 0, (
            "Please configure a propper App ID in config.py"
        )
        assert self.api.communi_token != "ENTER-YOUR-TOKEN-HERE", (
            "Please change the default token in config.py"
        )
        assert self.api.communi_server == "https://api.communiapp.de/rest", (
            "Are you sure your server is correct?"
        )

    def test_login(self) -> None:
        """Check that login is possible."""
        if self.api.session is not None:
            self.api.session.close()
        result = self.api.login()
        assert result

    def test_login_wrong_app(self) -> None:
        """Check incorrect logins."""
        temp_COMMUNI_APPID = self.api.communi_appid
        self.api.communi_appid = 9999
        if self.api.session is not None:
            self.api.session.close()
        result = self.api.login()
        assert not result

        self.api.communi_appid = temp_COMMUNI_APPID
        if self.api.session is not None:
            self.api.session.close()
        result = self.api.login()
        assert result

    def test_who_am_i(self) -> None:
        """Check if logged in user can be retrieved.

        This test tries to login with invalid credentials
        it will reset to original credentials afterwards.
        """
        # Make auth fail on purpose
        old_token = self.api.communi_token
        self.api.communi_token = "FAIL"  # noqa: S105

        self.api.login()
        result = self.api.who_am_i()
        assert not result

        self.api.communi_token = old_token
        self.api.login()

        result = self.api.who_am_i()
        assert isinstance(result, dict)
        assert result.get("id")
        assert result.get("firstName")
        assert result.get("lastName")
        assert result.get("mailadresse")

    def test_getUserList(self) -> None:
        """Check getUserList API.

        IMPORTANT - This test method and the parameters used depend on the target system!
        userId = 28057 => Admin
        """
        userId = 28057

        result = self.api.getUserList()
        assert len(result) > 0

        result = self.api.getUserList(userId=userId)
        assert "id" in result

    def test_getGroups(self) -> None:
        """Check getGroups API.

        IMPORTANT - This test method and the parameters used depend on the target system!
        """
        result = self.api.getGroups()
        assert len(result) > 0

        result = self.api.getGroups(id=7525)["title"]
        test_title = "Evang. Kirche Baiersbronn"
        assert result == test_title

        result = self.api.getGroups(name="Admins und Moderatoren")["id"]
        test_id = 7676
        assert result == test_id

    def test_createDeleteGroup(self) -> None:
        """Check create/delete Group APIs.

        Test that creates two new groups and deletes them one by id and one by name
        IMPORTANT - This test method and the parameters used depend on the target system!
        :return:
        """
        description = (
            "created by test_deleteGroup() function should be auto deleted after successful test\n"
            "feel free to delete this group manually if it still exists"
        )
        group1 = self.api.createGroup("Test1", description)
        group2 = self.api.createGroup("Test2", description)
        group2 = self.api.getGroups(id=group2["id"])

        result = self.api.deleteGroup(id=group1["id"])
        assert result

        result2 = self.api.deleteGroup(name=group2["title"])
        assert result2

    def test_userGroupList(self) -> None:
        """Check userGroupList.

        IMPORTANT - This test method and the parameters used depend on the target system!
        :return:
        """
        user_id = 28057
        group_id = self.api.createGroup(
            "_test_userGroupList ",
            "If this group exists some test failed - please delete",
        )["id"]
        self.api.changeUserGroup(userId=user_id, groupId=group_id, add_user=True)

        result = self.api.getUserGroupList()
        assert len(result) > 0

        result = self.api.getUserGroupList(user=user_id)
        assert len(result) > 1

        result = self.api.getUserGroupList(group=group_id)
        assert len(result) > 1

        result = self.api.getUserGroupList(group=group_id, user=user_id)
        assert len(result) == 1
        assert result[0]["user"] == user_id
        assert result[0]["group"] == group_id

        result = self.api.deleteGroup(id=group_id)
        assert result

    def test_changeUserGroup(self) -> None:
        """Check changeUserGroup API.

        Tries to add and remove a user from a test group
        IMPORTANT - This test method and the parameters used depend on the target system!
        Testing with userID 28057 (admin)  and groupID 21037 (_TEST Gruppe - UserAdd)
        """
        user_id = 28057
        group_id = self.api.createGroup(
            "_test_changeUserGroup ",
            "If this group exists some test failed - please delete",
        )["id"]

        assert not self.api.changeUserGroup(0, 0, add_user=False)
        assert self.api.changeUserGroup(user_id, group_id, add_user=True)

        test_result = self.api.getUserGroupList(user=user_id, group=group_id)
        assert len(test_result) == 1
        assert test_result[0]["status"] == 2

        assert not self.api.changeUserGroup(0, 0, add_user=False)
        assert self.api.changeUserGroup(user_id, group_id, add_user=False)
        test_result = self.api.getUserGroupList(user=user_id, group=group_id)
        assert test_result[0]["status"] == 4

        result = self.api.deleteGroup(id=group_id)
        assert result

    def test_message(self) -> None:
        """Check message API.

        Attempts to post a chat message text into a test group
        IMPORTANT - This test method and the parameters used depend on the target system!
        groupID 21037 (_TEST Gruppe - UserAdd)
        :return:
        """
        group_id = self.api.createGroup(
            "_test_message ", "If this group exists some test failed - please delete"
        )["id"]

        timestamp = datetime.now()
        result = self.api.message(
            groupId=group_id, text=f"Hello World from test_postInGroup - on {timestamp}"
        )
        assert result

        result = self.api.deleteGroup(id=group_id)
        assert result

    def test_create_event_chats(self) -> None:
        """Check create_event_chat functions.

        Testing method to check if event creation and user update works
        IMPORTANT - This test method and the parameters used depend on the target system!
        event ID 2626 on elkw1610.krz.tools represents a rest event with multiple services
        :return:
        """
        test_event_ids = [2626]
        result = create_event_chats(
            self.ct_api, self.api, test_event_ids, only_relevant=True
        )
        assert True is result

        result = delete_event_chats(self.ct_api, self.api, test_event_ids)
        assert True is result

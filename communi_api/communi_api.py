import json
import logging
import logging.config
from datetime import datetime
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

config_file = Path("logging_config.json")
with config_file.open(encoding="utf-8") as f_in:
    logging_config = json.load(f_in)
    log_directory = Path(logging_config["handlers"]["file"]["filename"]).parent
    if not log_directory.exists():
        log_directory.mkdir(parents=True)
    logging.config.dictConfig(config=logging_config)


class CommuniApi:
    """CommuniAPI class which can be used for all actions with Communi"""

    def __init__(self, communi_server, communi_token, communi_appid):
        """Args:
        communi_token (str): security token used for access - see /page/integration/tab/rest within communi as admin
        communi_server (str): REST endpoint of the server https://api.communiapp.de/rest by default
        communi_appid (int): app ID of the communi instance to be used - see /page/integration/tab/rest within communi as admin
        """
        super().__init__()
        self.communi_server = communi_server
        self.communi_token = communi_token
        self.communi_appid = communi_appid

        self.session = requests.Session()
        self.login()

        logger.debug("Instance initialized")

    def __str__(self):
        """Default print option for the class
        :return:
        """
        text = f"This is a Communi API instance connected to {self.communi_server} with CommuniApp {self.communi_appid}"
        return text

    def login(self):
        """Method used for login (with token, server stored in instance)
        :return:  either response content or False if unsucessful
        """
        url = self.communi_server + "/login"
        self.session.headers["X-Authorization"] = "Bearer " + self.communi_token

        response = self.session.get(url=url)
        if response.status_code == requests.codes.ok:
            response_content = json.loads(response.content)
            self.user_id = response_content["id"]
            logger.debug("Login with user ID:%s - success", self.user_id)

            groups = self.getGroups()
            if groups:
                return response_content
            logger.warning(
                "Login with App-ID:%s did not return groups - either APP-ID wrong or empty app",
                self.communi_appid,
            )
            return False
        if hasattr(self, "user_id"):
            del self.user_id
        logger.debug("Login failed with %s", response.content)
        return False

    def who_am_i(self):
        """Method to request user information associated with the logged in user (id stored upon successful login)
        This can be used to test if the user is authorized

        :return: dict of user OR bool False if not successful
        """
        if not hasattr(self, "user_id"):
            return False
        return self.getUserList(userId=self.user_id)

    def getUserList(self, **kwargs):
        """Method that requests the list of all users from Communi and optionally aplies filter by ID
        :param kwargs: keyword arguments
        :keyword userId: user Id to filter by
        :return: list of users or False if unsuccesful
        """
        url = self.communi_server + "/user"  # +'?communiApp=2406&loadStatus=1'
        params = {"communiApp": self.communi_appid, "loadStatus": 1}
        if "userId" in kwargs:
            params["id"] = kwargs["userId"]

        response = self.session.get(url=url, params=params)
        if response.status_code == requests.codes.ok:
            response_content = json.loads(response.content)
            logger.debug("Fetched %s users successful", len(response_content))
            return response_content
        logger.debug(
            "getUserList failed with code %s and message %s",
            response.status_code,
            response.content,
        )
        return False

    def getUserGroupList(self, **kwargs):
        """Get a list of UserGroup allocations matching respecting optional id and group id filter
        :param kwargs:
        :keyword group: group ID for filter
        :keyword user: user ID for filter
        :return: list of UserGroup allocations
        """
        url = self.communi_server + "/UserGroup"
        params = {"loadStatus": True, "communiApp": self.communi_appid}

        if "group" in kwargs:
            params["group"] = kwargs["group"]
        if "user" in kwargs:
            params["user"] = kwargs["user"]

        response = self.session.get(url=url, params=params)

        if response.status_code == requests.codes.ok:
            response_content = json.loads(response.content)
            if len(response_content) == 0:
                logger.debug(
                    "Response content empty - maybe group / user ID %s?", kwargs
                )
                return False
            logger.debug("Found %s assignments - success", len(response_content))
            return response_content
        logger.warning(
            "Requesting group / user assignements failed with %s", response.content
        )
        return False

    def createGroup(
        self, title="", description="", access_type_open=False, hasGroupChat=True
    ):
        """Method which creates a new group in Communi
        :param title: Name of the group
        :param description: Description for the group
        :param access_type_open: boolean set to true if open to everyone
        :param hasGroupChat: boolean set to true if chat should exist
        :return: response for group creation from communi or false if not successful
        """
        url = self.communi_server + "/group"
        data = {
            "title": title,
            "description": description,
            "type": "2",
            "accessType": "2" if access_type_open else "3",
            "hasGroupChat": hasGroupChat,
            "communiApp": self.communi_appid,
        }

        response = self.session.post(url=url, json=data)

        if response.status_code == requests.codes.ok:
            response_content = json.loads(response.content)
            if len(response_content) == 0:
                logger.debug("Response content empty - likely failed?")
                return False
            logger.debug("Created group id %s - success", response_content["id"])
            return response_content
        logger.debug("Creating group failed with %s", response.content)
        return False

    def getGroups(self, **kwargs):
        """Get a list of groups matching either any or keyword specified criteria
        :param kwargs:
        :keyword id: get only group with matching id
        :keyword name: get only group with matching name
        :return: list of groups or single group if filtered
        """
        url = self.communi_server + "/group"
        params = {"loadStatus": True, "communiApp": self.communi_appid}
        if "id" in kwargs:
            params["id"] = kwargs["id"]

        response = self.session.get(url=url, params=params)

        if response.status_code == requests.codes.ok:
            response_content = json.loads(response.content)
            if len(response_content) == 0:
                logger.debug(
                    "Response content empty - maybe group does not exist? %s?", kwargs
                )
                return False
            logger.debug("Found %s groups - success", len(response_content))

            if "name" in kwargs:
                response_content = [
                    item for item in response_content if item["title"] == kwargs["name"]
                ]
            return (
                response_content[0] if len(response_content) == 1 else response_content
            )
        logger.debug("Requesting group failed with %s", response.content)
        return False

    def deleteGroup(self, **kwargs):
        """Delete a groups matching keyword specified criteria
        :param kwargs: id = groupID (primary filter) OR name = groupName (without
        :return: True if group does not exist at end of function
        """
        by_name = "name" in kwargs

        if not (by_name or "id" in kwargs) and len(kwargs.keys() == 1):
            logger.warning("Problem with keywords %s in deleteGroupd", kwargs)
        else:
            id = (
                kwargs["id"]
                if "id" in kwargs
                else self.getGroups(name=kwargs["name"])["id"]
            )

        url = self.communi_server + "/group/" + str(id)

        response = self.session.delete(url)

        if response.status_code == requests.codes.ok:
            response_content = json.loads(response.content)
            if len(response_content) == 0:
                logger.debug("Deleted group%s?", id)
                return True
        else:
            logger.debug("Deleting group failed with %s", response.content)
            return False

    def changeUserGroup(self, userId, groupId, add_user=True):
        """Function to add or remove a user from a group
        Be aware that there might be a few seconds delay before changes are reflected in the app

        :param userId: user specific id
        :param groupId: group specific id- either from get groups or e.g. from groups detail page
        :param add_user: boolean if user should be added (or removed if false)
        :return: ???
        """
        url = self.communi_server + f"/UserGroup/{userId}-{groupId}"

        data = {
            "roleId": 40,
            "createdOn": str(datetime.now()),
            "status": 2 if add_user else 4,
            "user": userId,
            "group": groupId,
            "id": f"{userId}-{groupId}",
            "_rls": 1,
            "_loadStatus": 10,
            "valid": True,
        }

        response = self.session.put(url, json=data)

        if response.status_code == requests.codes.ok:
            response_content = json.loads(response.content)
            if "error" not in response_content.keys():
                if "valid" in response_content.keys():
                    logger.debug(
                        "Changed permissions of user %s on group %s?", userId, groupId
                    )
                    return response_content["valid"]
                return False
            return False
        logger.debug(
            "Changing assignment on user %s with group %s failed with %s",
            userId,
            groupId,
            response.content,
        )
        return False

    def message(self, groupId, text):
        """Posts a chat message into a communi group
        :param groupId: ID of the group to be used for posting
        :param text: The text which should be posted
        :return: true if success, false on error
        """
        url = self.communi_server + "/message"

        data = {"message": text, "conversation": f"group-{groupId}"}

        response = self.session.post(url, json=data)

        if response.status_code == requests.codes.ok:
            response_content = json.loads(response.content)
            if "error" not in response_content.keys():
                if "valid" in response_content.keys():
                    logger.debug("Posted message %s", data)
                    return response_content["valid"]
                return False
            return False
        logger.debug("Posting message %s failed with %s", data, response.content)
        return False

    def recommendation(  # noqa: PLR0913
        self,
        group_id: int,
        title: str,
        description: str,
        post_date: datetime,
        pic_url: str = "",
        is_official: bool = False,  # noqa: FBT001, FBT002
    ) -> bool:
        """Post a new recommendation into a group.

        Args:
            group_id: number of the group to post in
            title: title to be used
            description: text body used
            post_date: ? likely manual date of post
            pic_url: optional url to picture to be shown
            is_official: if posted as user or official. Defaults to False.

        Returns:
            if successful
        """
        url = self.communi_server + "/recommendation"

        data = {
            "title": title,
            "dateTime": post_date.strftime("%Y-%m-%d %H:%M:%S %z").replace(
                "+0000", "+0"
            ),
            "description": description,
            "picUrl": pic_url,
            "group": f"{group_id}",
            "isOfficial": is_official,
        }

        response = self.session.post(url, json=data)

        if response.status_code == requests.codes.ok:
            response_content = json.loads(response.content)
            if "error" not in response_content and "valid" in response_content:
                logger.debug("Posted message %s", data)
                return response_content["valid"]
        logger.debug("Posting message %s failed with %s", data, response.content)
        return False

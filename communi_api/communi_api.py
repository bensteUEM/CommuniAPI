"""This module implements functionality to use CommuniAPI with python."""

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
    """CommuniAPI class which can be used for all actions with Communi."""

    def __init__(
        self, communi_server: str, communi_token: str, communi_appid: int
    ) -> None:
        """Setup initial connection.

        Arguments:
            communi_token: security token used for access
                see /page/integration/tab/rest within communi as admin
            communi_server: REST endpoint of the server
                https://api.communiapp.de/rest by default
            communi_appid: app ID of the communi instance to be used
                see /page/integration/tab/rest within communi as admin.
        """
        super().__init__()
        self.communi_server = communi_server
        self.communi_token = communi_token
        self.communi_appid = communi_appid

        self.session = requests.Session()
        self.login()

        logger.debug("Instance initialized")

    def __str__(self) -> str:
        """Default print option for the class.

        Returns:
             String with basic information about the instance.
        """
        return (
            "This is a Communi API instance connected to"
            f" {self.communi_server} with CommuniApp {self.communi_appid}"
        )

    def login(self) -> dict | bool:
        """Method used for login (with token, server stored in instance).

        Returns:
            either response content or False if unsucessful.
        """
        url = self.communi_server + "/login"
        self.session.headers["X-Authorization"] = "Bearer " + self.communi_token

        response = self.session.get(url=url)
        if response.status_code == requests.codes.ok:
            response_content = json.loads(response.content)
            self.user_id = response_content["id"]
            logger.debug("Login with user ID:%s - success", self.user_id)

            groups = self.get_groups()
            if groups:
                return response_content
            logger.warning(
                "Login with App-ID:%s did not return groups -"
                " either APP-ID wrong or empty app",
                self.communi_appid,
            )
            return False
        if hasattr(self, "user_id"):
            del self.user_id
        logger.debug("Login failed with %s", response.content)
        return False

    def who_am_i(self) -> dict | bool:
        """Method to request user information associated with the logged in user.

        (id stored upon successful login)
        This can be used to test if the user is authorized.

        Returns.
            dict of user OR bool False if not successful
        """
        if not hasattr(self, "user_id"):
            return False
        return self.get_user_list(userId=self.user_id)

    def get_user_list(self, **kwargs: int) -> list | bool:
        """Method that requests the list of all users.

        from Communi and optionally aplies filter by ID.

        Arguments:
            kwargs: keyword arguments

        Keyword:
            userId: user Id to filter by

        Returns:
            list of users or False if unsuccesful.
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

    def get_user(self, user_id: int) -> dict | bool:
        """Request a single user by ID.

        Arguments: user_id: ID of the user to be requested
        Returns: dict of user information or False if not successful.
        """
        url = self.communi_server + f"/user/{user_id}"
        params = {"communiApp": self.communi_appid, "loadStatus": 1}

        response = self.session.get(url=url, params=params)
        if response.status_code == requests.codes.ok:
            response_content = json.loads(response.content)
            if isinstance(response_content, dict) and response_content:
                logger.debug("Fetched user %s successful", user_id)
                return response_content
            logger.warning("User %s response empty or invalid", user_id)
            return False
        logger.debug(
            "get_user failed with code %s and message %s",
            response.status_code,
            response.content,
        )
        return False

    def update_user(self, user_id: int, data: dict) -> dict | bool:
        """Update a user via PUT using the Communi User API.

        Following API documentation only own user can be updated!

        Arguments:
            user_id: ID of the user to be updated
            data: dict with user information to be updated.
            Must include all required fields.

        Returns:
            dict of updated user information or False if not successful.
        """
        url = self.communi_server + f"/user/{user_id}"

        payload = dict(data)
        payload["id"] = user_id
        payload["communiApp"] = self.communi_appid

        response = self.session.put(url=url, json=payload)
        if response.status_code == requests.codes.ok:
            response_content = json.loads(response.content)
            if isinstance(response_content, dict) and response_content:
                logger.debug("Updated user %s successful", user_id)
                return response_content
            logger.warning(
                "Update of user %s returned empty or invalid response",
                user_id,
            )
            return False
        logger.debug(
            "update_user failed with code %s and message %s",
            response.status_code,
            response.content,
        )
        return False

    def delete_user(self, user_id: int) -> bool:
        """Delete a user by ID.

        No test implemented because no create method exists in API

        Arguments:
            user_id: ID of the user to be deleted
        Returns:
            True if deletion successful, False otherwise.
        """
        url = self.communi_server + f"/user/{user_id}"

        response = self.session.delete(url)
        if response.status_code == requests.codes.ok:
            response_content = json.loads(response.content)
            if len(response_content) == 0:
                logger.debug("Deleted user %s successful", user_id)
                return True
        logger.debug("Deleting user %s failed with %s", user_id, response.content)
        return False

    def get_user_group_list(self, **kwargs: int) -> list | bool:
        """Get a list of UserGroup allocations matching.

        respecting optional id and group id filter.

        Arguments:
            kwargs: keyword arguments

        Keyword:
            group: group ID for filter
            user: user ID for filter
        Returns:
            list of UserGroup allocations.
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

    def create_group(
        self,
        title: str = "",
        description: str = "",
        access_type_open: bool = False,  # noqa: FBT001, FBT002
        has_goup_chat: bool = True,  # noqa: FBT001, FBT002
    ) -> dict | bool:
        """Method which creates a new group in Communi.

        Arguments:
            title: Name of the group
            description: Description for the group
            access_type_open: boolean set to true if open to everyone
            has_goup_chat: boolean set to true if chat should exist
        Returns:
            response for group creation from communi or false if not successful.
        """
        url = self.communi_server + "/group"
        data = {
            "title": title,
            "description": description,
            "type": "2",
            "accessType": "2" if access_type_open else "3",
            "hasGroupChat": has_goup_chat,
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

    def get_groups(self, **kwargs: int | str) -> list | dict | bool:
        """Get a list of groups matching either any or keyword specified criteria.

        Arguments:
             kwargs: keyword arguments

        Keywords:
            id: get only group with matching id
            name: get only group with matching name
        Returns:
            list of groups or single group if filtered.
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

    def delete_group(self, **kwargs: int | str) -> bool:
        """Delete a groups matching keyword specified criteria.

        Arguments:
             kwargs: keyword arguments

        Keywords:
             id: groupID (primary filter) OR name = groupName (without

        Returns:
            True if group does not exist at end of function.
        """
        by_name = "name" in kwargs

        if not (by_name or "id" in kwargs) and len(kwargs.keys() == 1):
            logger.warning("Problem with keywords %s in deleteGroupd", kwargs)
        else:
            group_id = (
                kwargs["id"]
                if "id" in kwargs
                else self.get_groups(name=kwargs["name"])["id"]
            )

        url = self.communi_server + "/group/" + str(group_id)

        response = self.session.delete(url)

        if response.status_code == requests.codes.ok:
            response_content = json.loads(response.content)
            if len(response_content) == 0:
                logger.debug("Deleted group%s?", group_id)
                return True

        logger.debug("Deleting group failed with %s", response.content)
        return False

    def change_user_group(
        self,
        user_id: int,
        group_id: int,
        add_user: bool = True,  # noqa: FBT001, FBT002
    ) -> bool:
        """Function to add or remove a user from a group.

        Be aware that there might be a few seconds delay
        before changes are reflected in the app.

        Arguments:
            user_id: user specific id
            group_id: group specific id- either from
                get groups or e.g. from groups detail page
            add_user: boolean if user should be added (or removed if false)

        Returns:
            ???
        """
        url = self.communi_server + f"/UserGroup/{user_id}-{group_id}"

        data = {
            "roleId": 40,
            "createdOn": str(datetime.now()),  # noqa: DTZ005
            "status": 2 if add_user else 4,
            "user": user_id,
            "group": group_id,
            "id": f"{user_id}-{group_id}",
            "_rls": 1,
            "_loadStatus": 10,
            "valid": True,
        }

        response = self.session.put(url, json=data)

        if response.status_code == requests.codes.ok:
            response_content = json.loads(response.content)
            if "error" not in response_content:
                if "valid" in response_content:
                    logger.debug(
                        "Changed permissions of user %s on group %s?", user_id, group_id
                    )
                    return response_content["valid"]
                return False
            return False
        logger.debug(
            "Changing assignment on user %s with group %s failed with %s",
            user_id,
            group_id,
            response.content,
        )
        return False

    def message(self, group_id: int, text: str) -> bool:
        """Posts a chat message into a communi group.

        Arguments:
            group_id: ID of the group to be used for posting
            text: The text which should be posted
        Returns:
            true if success, false on error.
        """
        url = self.communi_server + "/message"

        data = {"message": text, "conversation": f"group-{group_id}"}

        response = self.session.post(url, json=data)

        if response.status_code == requests.codes.ok:
            response_content = json.loads(response.content)
            if "error" not in response_content:
                if "valid" in response_content:
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
        link: str = "",
        is_official: bool = False,  # noqa: FBT001, FBT002
    ) -> bool:
        """Post a new recommendation into a group.

        Args:
            group_id: number of the group to post in
            title: title to be used
            description: text body used
            post_date: ? likely manual date of post
            pic_url: optional url to picture to be shown
            link: recommendation URL
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
            "link": link,
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

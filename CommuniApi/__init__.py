import json
import logging
from datetime import datetime

import requests

class CommuniApi:
    """ CommuniAPI class which can be used for all actions with Communi
    """

    def __init__(self, communi_server, communi_token, communi_appid):
        """

        Args:
            communi_token (str): security token used for access - see /page/integration/tab/rest within communi as admin
            communi_server (str): REST endpoint of the server https://api.communiapp.de/rest by default
            communi_appid (int): app ID of the communi instance to be used - see /page/integration/tab/rest within communi as admin
        """

        super().__init__()
        self.communi_server = communi_server
        self.communi_token = communi_token
        self.communi_appid = communi_appid

        logging.basicConfig(filename='logs/CommuniApi.log', encoding='utf-8',
                            format="%(asctime)s %(name)-10s %(levelname)-8s %(message)s",
                            level=logging.DEBUG)
        self.session = requests.Session()
        self.session.headers['X-Authorization'] = 'Bearer ' + self.communi_token
        self.login()

        logging.debug('Instance initialized')

    def __str__(self, ):
        """
        Default print option for the class
        :return:
        """
        text = "This is a Communi API instance connected to {} with CommuniApp {}".format(self.communi_server,
                                                                                          self.communi_appid)
        return text

    def login(self):
        """
        Method to confirm login id
        :return:  either response content or False if unsucessful
        """
        url = self.communi_server + '/login'
        response = self.session.get(url=url)
        if response.status_code == 200:
            response_content = json.loads(response.content)
            self.user_id = response_content['id']
            logging.debug("Login with user ID:{} - success".format(self.user_id))
            return response_content
        else:
            logging.debug("Login failed with {}".format(response.content))
            return False

    def who_am_i(self):
        """ Method to request user information associated with the logged in user (id stored upon successful login)
        This can be used to test if the user is authorized

        :return: dict of user OR bool False if not successful
        """

        userList = self.getUserList(userId=self.user_id)
        if userList == {'_loadStatus': '1', 'vorname': '', 'nachname': ''}:
            return False
        else:
            return self.getUserList(userId=self.user_id)

    def getUserList(self, **kwargs):
        """
        Method that requests the list of all users from Communi and optionally aplies filter by ID
        :param kwargs: keyword arguments
        :keyword userId: user Id to filter by
        :return: list of users or False if unsuccesful
        """
        url = self.communi_server + '/user'  # +'?communiApp=2406&loadStatus=1'
        params = {'communiApp': self.communi_appid,
                  'loadStatus': 1
                  }
        if 'userId' in kwargs.keys():
            params['id'] = kwargs['userId']

        response = self.session.get(url=url, params=params)
        if response.status_code == 200:
            response_content = json.loads(response.content)
            logging.debug("Fetched {} users successful".format(len(response_content)))
            return response_content
        else:
            logging.debug(
                "getUserList failed with code {} and message {}".format(response.status_code, response.content))
            return False

    def getUserGroupList(self, **kwargs):
        """
        Get a list of UserGroup allocations matching respecting optional id and group id filter
        :param kwargs:
        :keyword group: group ID for filter
        :keyword user: user ID for filter
        :return: list of UserGroup allocations
        """

        url = self.communi_server + '/UserGroup'
        params = {
            'loadStatus': True,
            'communiApp': self.communi_appid
        }

        if 'group' in kwargs.keys():
            params['group'] = kwargs['group']
        if 'user' in kwargs.keys():
            params['user'] = kwargs['user']

        response = self.session.get(url=url, params=params)

        if response.status_code == 200:
            response_content = json.loads(response.content)
            if len(response_content) == 0:
                logging.debug("Response content empty - maybe group / user ID {}?".format(kwargs))
                return False
            else:
                logging.debug("Found {} assignments - success".format(len(response_content)))
                return response_content
        else:
            logging.warning("Requesting group / user assignements failed with {}".format(response.content))
            return False

    def createGroup(self, title="", description="", access_type_open=False, hasGroupChat=True):
        """
        Method which creates a new group in Communi
        :param title: Name of the group
        :param description: Description for the group
        :param access_type_open: boolean set to true if open to everyone
        :param hasGroupChat: boolean set to true if chat should exist
        :return: response for group creation from communi or false if not successful
        """
        url = self.communi_server + '/group'
        data = {
            'title': title,
            'description': description,
            'type': '2',
            'accessType': '2' if access_type_open else '3',
            "hasGroupChat": hasGroupChat,
            "communiApp": self.communi_appid
        }

        response = self.session.post(url=url, json=data)

        if response.status_code == 200:
            response_content = json.loads(response.content)
            if len(response_content) == 0:
                logging.debug("Response content empty - likely failed?")
                return False
            else:
                logging.debug("Created group id {} - success".format(response_content['id']))
                return response_content
        else:
            logging.debug("Creating group failed with {}".format(response.content))
            return False

    def getGroups(self, **kwargs):
        """
        Get a list of groups matching either any or keyword specified criteria
        :param kwargs:
        :keyword id: get only group with matching id
        :keyword name: get only group with matching name
        :return: list of groups or single group if filtered
        """

        url = self.communi_server + '/group'
        params = {
            'loadStatus': True,
            'communiApp': self.communi_appid
        }
        if 'id' in kwargs.keys():
            params['id'] = kwargs['id']

        response = self.session.get(url=url, params=params)

        if response.status_code == 200:
            response_content = json.loads(response.content)
            if len(response_content) == 0:
                logging.debug("Response content empty - maybe group does not exist? {}?".format(kwargs))
                return False
            else:
                logging.debug("Found {} groups - success".format(len(response_content)))

                if 'name' in kwargs.keys():
                    response_content = [item for item in response_content if item['title'] == kwargs['name']]
                return response_content[0] if len(response_content) == 1 else response_content
        else:
            logging.debug("Requesting group failed with {}".format(response.content))
            return False

    def deleteGroup(self, **kwargs):
        """
        Delete a groups matching keyword specified criteria
        :param kwargs: id = groupID (primary filter) OR name = groupName (without
        :return: True if group does not exist at end of function
        """
        by_name = 'name' in kwargs.keys()

        if not (by_name or 'id' in kwargs.keys()) and len(kwargs.keys() == 1):
            logging.warning('Problem with keywords {} in deleteGroupd'.format(kwargs))
        else:
            id = kwargs['id'] if 'id' in kwargs.keys() else self.getGroups(name=kwargs['name'])['id']

        url = self.communi_server + '/group/' + str(id)

        response = self.session.delete(url)

        if response.status_code == 200:
            response_content = json.loads(response.content)
            if len(response_content) == 0:
                logging.debug("Deleted group{}?".format(id))
                return True
        else:
            logging.debug("Deleting group failed with {}".format(response.content))
            return False

    def changeUserGroup(self, userId, groupId, add_user=True):
        """
        Function to add or remove a user from a group
        Be aware that there might be a few seconds delay before changes are reflected in the app

        :param userId: user specific id
        :param groupId: group specific id- either from get groups or e.g. from groups detail page
        :param add_user: boolean if user should be added (or removed if false)
        :return: ???
        """

        url = self.communi_server + '/UserGroup/{}-{}'.format(userId, groupId)

        data = {
            "roleId": 40,
            "createdOn": str(datetime.now()),
            "status": 2 if add_user else 4,
            "user": userId,
            "group": groupId,
            "id": "{}-{}".format(userId, groupId),
            "_rls": 1,
            "_loadStatus": 10,
            "valid": True
        }

        response = self.session.put(url, json=data)

        if response.status_code == 200:
            response_content = json.loads(response.content)
            if 'error' not in response_content.keys():
                if 'valid' in response_content.keys():
                    logging.debug("Changed permissions of user {} on group {}?".format(userId, groupId))
                    return response_content['valid']
                else:
                    return False
            else:
                return False
        else:
            logging.debug(
                "Changing assignment on user {} with group {} failed with {}".format(userId, groupId, response.content))
            return False

    def message(self, groupId, text):
        """
        Posts a chat message into a communi group
        :param groupId: ID of the group to be used for posting
        :param text: The text which should be posted
        :return: true if success, false on error
        """

        url = self.communi_server + '/message'

        data = {
            "message": text,
            "conversation": "group-{}".format(groupId)
        }

        response = self.session.post(url, json=data)

        if response.status_code == 200:
            response_content = json.loads(response.content)
            if 'error' not in response_content.keys():
                if 'valid' in response_content.keys():
                    logging.debug("Posted message {}".format(data))
                    return response_content['valid']
                else:
                    return False
            else:
                return False
        else:
            logging.debug(
                "Posting message {} failed with {}".format(data, response.content))
            return False
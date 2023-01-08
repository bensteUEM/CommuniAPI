import json
import logging

import requests as requests

from secure.config import *


class CommuniApi:

    def __init__(self):
        super().__init__()
        self.rest_server = rest_server
        self.token = token
        self.communiAppId = communiAppId
        logging.basicConfig(filename='logs/CommuniApi.log', encoding='utf-8',
                            format="%(asctime)s %(name)-10s %(levelname)-8s %(message)s",
                            level=logging.DEBUG)
        self.session = requests.Session()
        self.session.headers['X-Authorization'] = 'Bearer ' + self.token

        logging.debug('Instance initialized')

    def __str__(self, ):
        """
        Default print option for the class
        :return:
        """
        text = "This is a Communi API instance connected to {} with CommuniApp {}".format(self.rest_server,
                                                                                          self.communiAppId)
        return text

    def login(self):
        """
        Method to confirm login id
        :return:  either response content or False if unsucessful
        """
        url = self.rest_server + '/login'
        response = self.session.get(url=url)
        if response.status_code == 200:
            response_content = json.loads(response.content)
            logging.debug("Login with user ID:{} - success".format(response_content['id']))
            return response_content
        else:
            logging.debug("Login failed with {}".format(response.content))
            return False

    def getUserList(self):
        """
        Method that requests the list of all users from Communi
        :return: list of users or False if unsuccesful
        """
        url = self.rest_server + '/user'  # +'?communiApp=2406&loadStatus=1'
        params = {'communiApp': self.communiAppId,
                  'loadStatus': 1
                  }
        response = self.session.get(url=url, params=params)
        if response.status_code == 200:
            response_content = json.loads(response.content)
            logging.debug("Fetched {} users successful".format(len(response_content)))
            return response_content
        else:
            logging.debug(
                "getUserList failed with code {} and message {}".format(response.status_code, response.content))
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
        url = self.rest_server + '/group'
        data = {
            'title': title,
            'description': description,
            'type': '2',
            'accessType': '2' if access_type_open else '3',
            "hasGroupChat": hasGroupChat,
            "communiApp": self.communiAppId
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


if __name__ == '__main__':
    api = CommuniApi()
    print(api)

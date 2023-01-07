import logging

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
        logging.debug('Instance initialized')

    def __str__(self,):
        """
        Default print option for the class
        :return:
        """
        text = "This is a Communi API instance connected to {} with CommuniApp {}".format(self.rest_server,
                                                                                          self.communiAppId)
        return text


if __name__ == '__main__':
    api = CommuniApi()
    print(api)

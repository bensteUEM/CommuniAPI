import logging

from CommuniAPI.CommuniApi import CommuniApi
from CommuniAPI.churchToolsActions import get_x_day_event_ids, delete_event_chats, create_event_chats

logging.basicConfig(filename='logs/CommuniApi.log', encoding='utf-8',
                    format="%(asctime)s %(name)-10s %(levelname)-8s %(message)s",
                    level=logging.DEBUG)

if __name__ == '__main__':
    print('To use this module please create an instance of the CommuniApi Module')
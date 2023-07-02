import logging
from datetime import datetime


def get_create_or_delete_group(communi_api, group_name, delete=False):
    """
    Function to check if the group (by name) exists and return it's communi_id
    in case the name is not found the group will be created
    :param communi_api: link to Communi
    :type communi_api: CommuniApi
    :param group_name: formatted event name from CT used as prefix for group name
    :param delete: bool whether it should be deleted (and not created if not found)
    :return: group ID if successful, None if not available
    :rtype: int
    """
    communi_groups = communi_api.getGroups()
    for group in communi_groups:
        if group['title'].startswith(group_name):
            if delete:
                result = communi_api.deleteGroup(id=group['id'])
                logging.debug('Deleted group {} was succesful = {}'.format(group['id'], result))

            return group['id']

    if not delete:
        event_description = \
        'Automatisch erstellte Gruppe für die Diskussion zur im Titel angegeben Veranstaltung' \
        ' Alle in ChurchTools beteiligten Personen werden mit ca. 2 Wochen Vorlauf hinzugefügt' \
        ' (Ausnahme - Die Dienste Begrüßung/Opfer werden nicht automatisch hinzugefügt)' \
        ' Fehlende/ Aktualisierte Personen werden sporadisch mit neuen Wochen aktualisiert' \
        ' - ACHTUNG - Wenige Tage nach Veranstaltung wird die Gruppe wieder gelöscht!'
        newGroup = communi_api.createGroup(group_name, event_description, False, True)
        return newGroup['id']
    else:
        logging.info("Group ({}) not found therefore not deleted".format(group_name))


def update_group_users_by_services(communi_api, event_services, groupId):
    """
    :param communi_api: link to Communi
    :type communi_api: CommuniApi.CommuniApi
    :param event_services:
    :type event_services: dict
    :param groupId: Communi Group ID != CT Group or Event ID
    :type groupId: int
    :return:
    """
    timestamp = datetime.now().astimezone().strftime('%a %d.%m (%H:%M:%S)')

    communi_users = communi_api.getUserList()
    communi_users_ids = {item['mailadresse']: item['id'] for item in communi_users}

    user_group_list = [user['user'] for user in communi_api.getUserGroupList(group=groupId)]
    new_group = len(user_group_list) == 1
    if new_group:
        text = 'Erstbefüllung der Gruppe mit Diensten'
    else:
        text = 'Aktualisierung der Gruppe mit aktuellen Diensten'

    communi_api.message(groupId=groupId, text='AUTOMATISCHE Nachricht {}\n'.format(timestamp) + text)

    for service_group_name, service_item in event_services.items():
        if len(service_item) == 0:  # Skip if empty Service Group
            continue
        text = ''
        for service_name, service_persons in service_item.items():
            user_name_text = ''
            for user in service_persons:
                mail = user[0]
                name = user[1]
                logging.debug('Trying to match {} of user {} for service {}'.format(mail, name, service_name))
                if service_name in ['Begrüßung & Opferzählen', 'Opfer zählen']:
                    logging.debug('not adding User {} with mail {} because of service name'.format(name, mail))
                    user_name_text += '\n• {} - (für Gruppe ausgelassen)'.format(name)
                elif mail in communi_users_ids.keys():
                    communi_user_id = communi_users_ids[mail]
                    logging.debug('User {} found in communi'.format(mail))
                    if new_group or (communi_user_id not in user_group_list):
                        logging.debug('User {} not found in group {}'.format(mail, groupId))
                        user_name_text += '\n• {}'.format(name)
                        communi_api.changeUserGroup(communi_user_id, groupId, True)
                else:
                    user_name_text += '\n• {} - FEHLT - (Mailadresse unbekannt)'.format(name)
                    logging.debug('User {} with mail {} NOT found in communi'.format(name, mail))
            if len(user_name_text) > 1:
                text += '\n' + service_name
                text += user_name_text
        if len(text) > 0:
            text = '{}:'.format(service_group_name) + text
            communi_api.message(groupId=groupId, text=text)

    timestamp = datetime.now().astimezone().strftime('%a %d.%m (%H:%M:%S)')
    communi_api.message(groupId=groupId, text='ENDE AUTOMATISCHE Nachricht  um {}'.format(timestamp))

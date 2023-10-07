import logging
from datetime import datetime, timedelta
from communi_api.communiActions import get_create_or_delete_group


def generate_group_name_for_event(ct_api, eventId):
    """
    Method to generate communi group name for an event
    :param ct_api: link to ChurchTools
    :type ct_api: ChurchToolsApi
    :param eventId: number of the event to load
    :type eventId: int
    :return: group_name
    :rtype: str
    """
    event = ct_api.get_events(eventId=eventId)[0]

    date = datetime.strptime(event['startDate'], "%Y-%m-%dT%H:%M:%S%z")
    datestring = date.astimezone().strftime('%a %d.%m (%H:%M)')

    group_name = '_{} - {}'.format(datestring, event['name'])

    logging.debug(
        'Generated name (%s) for event %s',
        group_name, eventId)

    return group_name


def are_services_relevant(eventServices):
    """
    Helper function which determines if the services for an event are considered relevant
    At present this requires at least 1 service in Technik
    This depends on your ChurchTools Data!
    :param eventServices: result of generate_services_for_event function
    :type eventServices: dict
    :return: if the set of event services should be considered relevant
    :rtype: bool
    """

    if 'Technik' in eventServices:
        if len(eventServices['Technik']) > 0:
            return True
    return False


def generate_services_for_event(ct_api, eventId):
    """
    Prepare the services variable used with Communi API for group automatisation
    :param ct_api: link to ChurchTools
    :type ct_api: ChurchToolsApi
    :param eventId: number of the event to load
    :type eventId: int
    :return: eventServices as lists of names per dict of service per dict of servicegroup
    :rtype: dict
    """
    logging.info("Trying to get list of involved persons for next event")
    event = ct_api.get_events(eventId=eventId, include='eventServices')[0]
    service_names = ct_api.get_services(returnAsDict=True)

    serviceGroups = ct_api.get_event_masterdata(
        type='serviceGroups', returnAsDict=True)
    eventServices = {item['name']: {} for item in serviceGroups.values()}

    for service in event['eventServices']:
        service_name_item = service_names[service['serviceId']]
        service_name = service_name_item['name']
        service_group_name = serviceGroups[service_name_item['serviceGroupId']]['name']
        if service_name not in eventServices[service_group_name].keys():
            eventServices[service_group_name][service_name] = []
        if service['personId'] is not None:
            personFromCT = ct_api.get_persons(ids=[service['personId']])[0]
            person = (
                personFromCT['email'],
                f"{'' if service['agreed'] else '?'} {personFromCT['firstName']} {personFromCT['lastName']}")
            eventServices[service_group_name][service_name].append(person)

    logging.debug('generate_services_for_event')

    return eventServices


def get_x_day_event_ids(
        ct_api, reference_day=datetime.today(), number_of_days=7):
    """
    Helper function that will get a list of event ids from CT based on reference day and number of days
    :param ct_api: link to ChurchTools
    :type ct_api: ChurchToolsApi
    :param number_of_days: number of days to take into consideration, by default 7 days, use negative numbers if needed
    :type number_of_days: int
    :param reference_day: reference day for relative event search
    :type reference_day: datetime
    :return: list of event ids from churchTools
    :rtype: list
    """

    target_day = reference_day + timedelta(number_of_days)

    if reference_day < target_day:
        from_date = reference_day.astimezone().strftime('%Y-%m-%d')
        to_date = target_day.astimezone().strftime('%Y-%m-%d')
    else:
        from_date = target_day.astimezone().strftime('%Y-%m-%d')
        to_date = reference_day.astimezone().strftime('%Y-%m-%d')

    events = ct_api.get_events(from_=from_date, to_=to_date)
    event_ids = [event['id'] for event in events]
    return event_ids


def delete_event_chats(ct_api, communi_api, event_ids):
    """
    Helper that deletes all groups that follow the automatic pattern for the last 14 days including today
    :param ct_api: link to ChurchTools
    :type ct_api: ChurchToolsApi
    :param communi_api: link to Communi
    :type communi_api: CommuniApi
    :param event_ids: list of CT event IDs to take into account
    :type event_ids: list
    :return: True if successful for all groups
    """

    result = True

    for event_id in event_ids:
        group_name = generate_group_name_for_event(ct_api, event_id)
        result |= get_create_or_delete_group(
            communi_api, group_name, delete=True) is not None

    return result


def create_event_chats(ct_api, communi_api, event_ids, only_relevant=True):
    """
    Helper that create all groups for the respective event_ids
    :param ct_api: link to ChurchTools
    :type ct_api: ChurchToolsApi
    :param communi_api: link to Communi
    :type communi_api: CommuniApi
    :param event_ids: list of CT event IDs to take into account
    :type event_ids: list
    :param only_relevant: if true - filter for relevant groups is applied
    :type only_relevant: bool
    :return: True if successful for all groups
    """

    result = True

    for event_id in event_ids:
        services = generate_services_for_event(ct_api, event_id)
        relevant = are_services_relevant(services)
        if (relevant and only_relevant) or not only_relevant:
            group_name = generate_group_name_for_event(ct_api, event_id)
            group_id = get_create_or_delete_group(
                communi_api, group_name, delete=False)
            result |= group_id is not None
            update_group_users_by_services(communi_api, services, group_id)

    return result


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
    communi_users_ids = {item['mailadresse']: item['id']
                         for item in communi_users}

    user_group_list = [user['user']
                       for user in communi_api.getUserGroupList(group=groupId)]
    new_group = len(user_group_list) == 1
    if new_group:
        text = 'Erstbefüllung der Gruppe mit Diensten'
    else:
        text = 'Aktualisierung der Gruppe mit aktuellen Diensten'

    communi_api.message(
        groupId=groupId,
        text='AUTOMATISCHE Nachricht {timestamp}\n' + text)

    for service_group_name, service_item in event_services.items():
        if len(service_item) == 0:  # Skip if empty Service Group
            continue
        text = ''
        for service_name, service_persons in service_item.items():
            user_name_text = ''
            for user in service_persons:
                mail = user[0]
                name = user[1]
                logging.debug(
                    'Trying to match %s of user %s for service %s',
                    mail, name, service_name)
                if service_name in ['Begrüßung & Opferzählen', 'Opfer zählen']:
                    logging.debug(
                        'not adding User %s with mail %s because of service name',
                        name, mail)
                    user_name_text += f'\n• {name} - (für Gruppe ausgelassen)'
                elif mail in communi_users_ids.keys():
                    communi_user_id = communi_users_ids[mail]
                    logging.debug('User %s found in communi', mail)
                    if new_group or (communi_user_id not in user_group_list):
                        logging.debug(
                            'User %s not found in group %s',
                            mail, groupId)
                        user_name_text += f'\n• {name}'
                        communi_api.changeUserGroup(
                            communi_user_id, groupId, True)
                else:
                    user_name_text += f'\n• {name} - FEHLT - (Mailadresse unbekannt)'
                    logging.debug(
                        'User %s with mail %s NOT found in communi',
                        name, mail)
            if len(user_name_text) > 1:
                text += '\n' + service_name
                text += user_name_text
        if len(text) > 0:
            text = f'{service_group_name}:' + text
            communi_api.message(groupId=groupId, text=text)

    timestamp = datetime.now().astimezone().strftime('%a %d.%m (%H:%M:%S)')
    communi_api.message(
        groupId=groupId,
        text=f'ENDE AUTOMATISCHE Nachricht  um {timestamp}')

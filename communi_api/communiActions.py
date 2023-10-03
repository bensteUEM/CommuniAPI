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
                logging.debug(
                    'Deleted group {} was succesful = {}'.format(
                        group['id'], result))

            return group['id']

    if not delete:
        event_description = \
            'Automatisch erstellte Gruppe für die Diskussion zur im Titel angegeben Veranstaltung' \
            ' Alle in ChurchTools beteiligten Personen werden mit ca. 2 Wochen Vorlauf hinzugefügt' \
            ' (Ausnahme - Die Dienste Begrüßung/Opfer werden nicht automatisch hinzugefügt)' \
            ' Fehlende/ Aktualisierte Personen werden sporadisch mit neuen Wochen aktualisiert' \
            ' - ACHTUNG - Wenige Tage nach Veranstaltung wird die Gruppe wieder gelöscht!'
        newGroup = communi_api.createGroup(
            group_name, event_description, False, True)
        return newGroup['id']
    else:
        logging.info(
            "Group ({}) not found therefore not deleted".format(group_name))

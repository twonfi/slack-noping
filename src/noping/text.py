"""Mention text functions.

This module includes things like text parsing and replacement.
"""

import re
from re import Match


def mentions_to_links(text: str, team_domain: str, client = None) -> str:
    """Convert Slack mentions ("<@...>") to links to the user's profile.

    :param text: Text with mentions to be converted
    :type text: str
    :param team_domain: Domain of the Slack workspace
    :type team_domain: str
    :param client: Slack client to use to retrieve a user's profile
    name. If None, use the internal "username" in the Slack account
    settings.
    :return: Text with links from mentioned users' IDs
    :rtype: str
    """

    def _repl(m):
        if client:
            profile_name = client.users_profile_get(
                user=m.group("user_id")).data["profile"]["display_name"]
        else:
            profile_name = m.group("username")
        return (fr"<https://{team_domain}.slack.com/team/{m.group("user_id")}"
                fr"|@{profile_name}>")

    return re.sub(
        r"<@(?P<user_id>[^|]*)\|(?P<username>.*)>(?! ?\\)",
        _repl,
        text
    )


def user_owns_message(text: str, user: str) -> bool:
    """Check if the user "owns" a message given its text.

    :param text: Message text
    :type text: str
    :param user: User ID to check against
    :type user: str
    :return: Whether the user owns the message
    :rtype: bool
    """

    try:
        return (re.match(r"^\*<@(?P<user_id>[^|]*)>\* via NoPing:",
            text).group("user_id") == user)
    except AttributeError:
        return False

import os
from json import dumps, loads

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.errors import SlackApiError

from noping import text

load_dotenv()


# noinspection PyUnusedLocal
def _build_blocks(client, user_id, content, team_domain) -> list:
    if type(content) == list:
        body = {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_section",
                    "elements": text.block_kit_mentions_to_links(
                        content,
                        team_domain,
                        client,
                    ),
                }
            ]
        }
    else:
        body = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text.mentions_to_links(content, team_domain,
                    app.client)
            }
        }

    return [
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"*<@{user_id}>*:"
                }
            ]
        }
    ] + [body]


def _build_message_editor_blocks(user_id: str) -> list:
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Mentions will be depinged unless they're"
                        r" followed by `\`."
            },
        },
        {
            "type": "divider"
        },
        {
            "type": "input",
            "element": {
                "type": "rich_text_input",
                "action_id": "rich_text_input-action",
            },
            "label": {
                "type": "plain_text",
                "text": f"<@{user_id}>:",
            },
        },
    ]


def _get_message_editor_input(view):
    return view["state"]["values"][view["blocks"][-1]["block_id"]][
        "rich_text_input-action"]["rich_text_value"]["elements"][0]["elements"]


def _post_noping_message(client, profile, user_id, blocks, trigger_id,
                         **kwargs):
    profile_name = (
        profile["display_name"]
        or profile["real_name"]
    )

    try:  # To show a modal if the conversation is inaccessible
        m = client.chat_postMessage(
            text=f"*<@{user_id}>*: ...",
            blocks=blocks,
            username=profile_name,
            icon_url=profile["image_512"],
            **kwargs
        )
    except SlackApiError as e:
        if e.response["error"] != "channel_not_found":
            raise  # Slack returned a different error

        # Slack returned "channel_not_found" meaning it's inaccessible
        # Show the modal
        client.views_open(
            trigger_id=trigger_id,
            view={
                "type": "modal",
                "title": {
                    "type": "plain_text",
                    "text": "Can't access channel",
                },
                "close": {
                    "type": "plain_text",
                    "text": "Close",
                },
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "NoPing is not in this private channel "
                                    "and cannot send messages in it. "
                                    "Try inviting NoPing with `/invite`.",
                        },
                    },
                    { "type": "divider" },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "plain_text",
                                "text": "Preview of your message:",
                                "emoji": False,
                            }
                        ]
                    }
                ] + blocks,
            },
        )
    else:
        return m


app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)


@app.command("/np")
def np(ack, client, command):
    ack()
    if command["text"].strip():
        user = client.users_info(user=command["user_id"])["user"]
        _post_noping_message(
            client,
            user["profile"],
            command["user_id"],
            blocks=_build_blocks(client, command["user_id"], command["text"],
                command["team_domain"]),
            trigger_id=command["trigger_id"],
            channel=command["channel_id"],
        )
    else:
        try:
            client.chat_postEphemeral(
                text="There's nothing for me to send!"
                     " Use `/np <message>` to send a message without pings,"
                     r" and use `@... \` in your message to escape a ping.",
                channel=command["channel_id"],
                user=command["user_id"],
            )
        except SlackApiError as e:
            if e.response["error"] != "channel_not_found":
                raise

            client.views_open(
                trigger_id=command["trigger_id"],
                view={
                    "type": "modal",
                    "title": {
                        "type": "plain_text",
                        "text": "Can't access channel",
                    },
                    "close": {
                        "type": "plain_text",
                        "text": "Close",
                    },
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "There's nothing for me to send in "
                                        "this private channel. To use `/np` "
                                        "to send directly, use `/invite` to "
                                        "add me first. You can also use "
                                        "`/npp` to preview a message in any "
                                        "channel."
                            },
                        },
                    ],
                },
            )


@app.command("/npp")
def npp(ack, client, command):
    """Send an ephemeral message similar to ``/np`` for previewing."""

    ack()
    preview_header = [
        {
            "type": "context",
            "elements": [{
                "type": "mrkdwn",
                "text": "This is only a preview; "
                        "*your message hasn't been sent yet!*"
            }],
        },
        {
            "type": "divider",
        },
    ]

    if command["text"].strip():
        blocks = _build_blocks(
            client,
            command["user_id"],
            command["text"],
            command["team_domain"]
        )

        try:  # Usual method: Ephemeral message
            client.chat_postEphemeral(
                blocks=preview_header + blocks,
                channel=command["channel_id"],
                user=command["user_id"],
            )
        except SlackApiError as e:
            if e.response["error"] != "channel_not_found":
                raise
            # Use a modal instead
            client.views_open(
                trigger_id=command["trigger_id"],
                view={
                    "type": "modal",
                    "title": {
                        "type": "plain_text",
                        "text": "Message preview",
                    },
                    "close": {
                        "type": "plain_text",
                        "text": "Close",
                    },
                    "blocks": preview_header + [
                        {
                            "type": "context",
                            "elements": [{
                                "type": "plain_text",
                                "text": "You're seeing this because NoPing is "
                                        "not in this private channel."
                            }],
                        },
                        {
                            "type": "divider",
                        },
                    ] + blocks,
                },
            )
    else:
        try:
            client.chat_postEphemeral(
                text="I can't preview an empty string. Check `/np` for usage.",
                channel=command["channel_id"],
                user=command["user_id"],
            )
        except SlackApiError as e:
            if e.response["error"] != "channel_not_found":
                raise
            client.views_open(
                trigger_id=command["trigger_id"],
                view={
                    "type": "modal",
                    "title": {
                        "type": "plain_text",
                        "text": "Nothing to preview",
                    },
                    "close": {
                        "type": "plain_text",
                        "text": "Close",
                    },
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "plain_text",
                                "text": "I can't preview an empty string. See "
                                        "my description for usage. "
                                        "You're seeing this because NoPing is "
                                        "not in this private channel."
                            },
                        },
                    ],
                },
            )


@app.message_shortcut("reply_thread")
def reply_thread(ack, client, shortcut):
    ack()
    client.views_open(
        trigger_id=shortcut["trigger_id"],
        view={
            "callback_id": "reply_thread",
            "private_metadata": dumps({
                "ts": shortcut["message"]["ts"],
                "ch": shortcut["channel"]["id"],
            }),
            "type": "modal",
            "title": {
                "type": "plain_text",
                "text": "Reply in thread"
            },
            "submit": {
                "type": "plain_text",
                "text": "Submit"
            },
            "close": {
                "type": "plain_text",
                "text": "Cancel"
            },
            "blocks": _build_message_editor_blocks(shortcut["user"]["id"]),
        },
    )


@app.view("reply_thread")
def handle_reply_thread(ack, client, view, body):
    ack()
    meta = loads(view["private_metadata"])

    user = client.users_info(user=body["user"]["id"])["user"]
    _post_noping_message(
        client,
        user["profile"],
        body["user"]["id"],
        blocks=_build_blocks(
            client,
            body["user"]["id"],
            _get_message_editor_input(view),
            body["team"]["domain"]
        ),
        trigger_id=body["trigger_id"],
        channel=meta["ch"],
        thread_ts=meta["ts"],
    )


# noinspection PyUnusedLocal
def _user_can_edit_message(client, msg_bot_id, msg_text, user_id) -> bool:
    return (msg_bot_id == client.auth_test().data["bot_id"]
            and text.user_owns_message(msg_text, user_id))


# noinspection PyUnusedLocal
@app.message_shortcut("delete_message")
def delete_message(ack, shortcut, client):
    """A stubbed function to respond to ``delete_message`` shortcuts.

    This was previously implemented but is now commented out as message
    deletion with an impersonated username is only possible with an
    admin token, which is likely not possible for the Hack Club Slack.
    """
    ack()
    client.views_open(
        trigger_id=shortcut["trigger_id"],
        view={
            "type": "modal",
            "title": {
                "type": "plain_text",
                "text": "Out of order",
            },
            "close": {
                "type": "plain_text",
                "text": "Close",
            },
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Due to NoPing's \"impersonation\", it cannot "
                                "delete messages. Use `/npp` to preview "
                                "messages and manually send them to have "
                                "control over your messages. "
                                "Editing is unaffected.",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "(Slack prevents impersonated messages from "
                                "being deleted by the bot who sent it. "
                                "Allowing deletion requires a highly "
                                "privileged and insecure admin token.)",
                    },
                }
            ],
        },
    )


@app.view("delete_message")
def handle_delete_message(ack, client, view):
    ack()
    meta = loads(view["private_metadata"])
    client.chat_delete(
        channel=meta["ch"],
        ts=meta["ts"]
    )


@app.message_shortcut("edit_message")
def edit_message(ack, shortcut, client):
    ack()
    if ("bot_id" in shortcut["message"]  # Prevents KeyError
            and _user_can_edit_message(client,
                shortcut["message"]["bot_id"],
                shortcut["message"]["text"],
                shortcut["user"]["id"])):
        client.views_open(
            trigger_id=shortcut["trigger_id"],
            view={
                "callback_id": "edit_message",
                "private_metadata": dumps({
                    "ts": shortcut["message"]["ts"],
                    "ch": shortcut["channel"]["id"],
                }),
                "type": "modal",
                "title": {
                    "type": "plain_text",
                    "text": "Edit message"
                },
                "submit": {
                    "type": "plain_text",
                    "text": "Submit"
                },
                "close": {
                    "type": "plain_text",
                    "text": "Cancel"
                },
                "blocks": _build_message_editor_blocks(shortcut["user"]["id"]),
            },
        )
    else:
        client.views_open(
            trigger_id=shortcut["trigger_id"],
            view={
                "type": "modal",
                "title": {
                    "type": "plain_text",
                    "text": "Can't edit message",
                },
                "close": {
                    "type": "plain_text",
                    "text": "Close",
                },
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "plain_text",
                            "text": "This message wasn't sent using NoPing or"
                                    " was sent by someone else.",
                        },
                    },
                ],
            },
        )


@app.view("edit_message")
def handle_edit_message(ack, client, view, body):
    ack()
    meta = loads(view["private_metadata"])
    client.chat_update(
        channel=meta["ch"],
        ts=meta["ts"],
        blocks=_build_blocks(client, body["user"]["id"],
            _get_message_editor_input(view), body["team"]["domain"]),
    )


if __name__ == "__main__":
    if os.environ.get("DEBUG") == "True":  # If explicitly in debug
        SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()

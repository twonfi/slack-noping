import os
import re
from time import sleep
from json import dumps, loads

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from noping import text

load_dotenv()


def _build_blocks(client, user_id, content, team_domain) -> list:
    if type(content) == list:
        for i, elem in enumerate(content):
            if elem["type"] == "user":
                if i+1 < len(content) and (
                    content[i+1]["type"] == "text"
                    and re.match(r"^ ?\\", content[i+1]["text"])
                ):
                    continue
                content[i] = {
                    "type": "link",
                    "text": "@" + client.users_profile_get(
                        user=elem["user_id"]
                    ).data["profile"]["display_name"],
                    "url": f"https://{team_domain}.slack.com"
                           f"/team/{elem["user_id"]}"
                }
        body = {
            "type": "rich_text",
            "elements": [
                {
                    "type": "rich_text_section",
                    "elements": content
                }
            ]
        }
    else:
        body = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text.mentions_to_links(content, team_domain, app.client)
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


def _post_pre_edit_message(client, profile, user_id, **kwargs):
    profile_name = (
        profile["display_name"]
        or profile["full_name"]
    )

    m = client.chat_postMessage(
        text=f"*<@{user_id}>*: ...",
        blocks=[
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"*<@{user_id}>*: ..."
                    }
                ]
            }
        ],
        username=profile_name,
        icon_url=profile["image_512"],
        **kwargs
    )
    sleep(.75)  # To prevent the automatic link preview
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
        m = _post_pre_edit_message(
            client,
            user["profile"],
            command["user_id"],
            channel=command["channel_id"],
        )
        client.chat_update(
            channel=m.data["channel"],
            ts=m.data["ts"],
            blocks=_build_blocks(client, command["user_id"], command["text"],
                command["team_domain"])
        )
    else:
        client.chat_postEphemeral(
            text="There's nothing for me to send!"
                 " Use `/np <message>` to send a message without pings,"
                 r" and use `@... \` in your message to escape a ping.",
            channel=command["channel_id"],
            user=command["user_id"],
        )


@app.command("/npp")
def npp(ack, client, command):
    """Send an ephemeral message similar to ``/np`` for previewing."""

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

    ack()
    if command["text"].strip():
        client.chat_postEphemeral(
            blocks=preview_header + _build_blocks(
                client,
                command["user_id"],
                command["text"],
                command["team_domain"]
            ),
            channel=command["channel_id"],
            user=command["user_id"],
        )
    else:
        client.chat_postEphemeral(
            text="I can't preview an empty string. Check `/np` for usage.",
            channel=command["channel_id"],
            user=command["user_id"],
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
    m = _post_pre_edit_message(
        client,
        user["profile"],
        body["user"]["id"],
        channel=meta["ch"],
        thread_ts=meta["ts"],
    )
    client.chat_update(
        channel=meta["ch"],
        ts=m.data["ts"],
        blocks=_build_blocks(client, body["user"]["id"],
            _get_message_editor_input(view), body["team"]["domain"]),
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

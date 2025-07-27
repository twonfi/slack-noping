import os
import re
from time import sleep
from json import dumps, loads

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from noping import text

load_dotenv()

app = App(token=os.environ.get("SLACK_BOT_TOKEN"))


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
                    "text": f"*<@{user_id}>:*"
                }
            ]
        }
    ] + [body]


@app.command("/np")
def np(ack, client, say, command):
    ack()
    if command["text"].strip():
        m = say(f":beachball: Incoming message from"
                f" <@{command["user_id"]}>...")
        sleep(.5)  # To prevent the automatic link preview
        client.chat_update(
            channel=m.data["channel"],
            ts=m.data["ts"],
            blocks=_build_blocks(client, command["user_id"], command["text"],
                command["team_domain"])
        )
    else:
        app.client.chat_postEphemeral(
            text="There's nothing for me to send!"
                 " Use `/np <message>` to send a message without pings,"
                 r" and use `@... \` in your message to escape a ping.",
            channel=command["channel_id"],
            user=command["user_id"],
        )


def _user_can_edit_message(client, msg_user_id, msg_text, user_id) -> bool:
    return (msg_user_id == client.auth_test().data["user_id"]
            and text.user_owns_message(msg_text, user_id))


@app.message_shortcut("delete_message")
def delete_message(ack, shortcut, client):
    ack()
    if _user_can_edit_message(client,
            shortcut["message"]["user"],
            shortcut["message"]["text"],
            shortcut["user"]["id"]):
        client.views_open(
            trigger_id=shortcut["trigger_id"],
            view={
                "callback_id": "delete_message",
                "private_metadata": dumps({
                    "ts": shortcut["message"]["ts"],
                    "ch": shortcut["channel"]["id"],
                }),
                "type": "modal",
                "title": {
                    "type": "plain_text",
                    "text": "Delete message"
                },
                "submit": {
                    "type": "plain_text",
                    "text": "Delete"
                },
                "close": {
                    "type": "plain_text",
                    "text": "Cancel"
                },
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "plain_text",
                            "text": "Are you sure you want to delete this"
                                    " message? This cannot be undone."
                        }
                    }
                ]
            }
        )
    else:
        client.views_open(
            trigger_id=shortcut["trigger_id"],
            view={
                "type": "modal",
                "title": {
                    "type": "plain_text",
                    "text": "Can't delete message",
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
    if _user_can_edit_message(client,
            shortcut["message"]["user"],
            shortcut["message"]["text"],
            shortcut["user"]["id"]):
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
                "blocks": [
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
                            "text": f"<@{shortcut["user"]["id"]}>:",
                        },
                    },
                ]
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
        blocks=_build_blocks(client, body["user"]["id"], view["state"]["values"][view["blocks"][-1]["block_id"]]["rich_text_input-action"]["rich_text_value"]["elements"][0]["elements"], body["team"]["domain"])  # Don't show this to Pythonistas!
    )


if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()

import os

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from noping import text

load_dotenv()

app = App(token=os.environ.get("SLACK_BOT_TOKEN"))


@app.command("/np")
def np(ack, say, command):
    ack()
    if command["text"].strip():
        say(blocks=[
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"*<@{command["user_id"]}>:*"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": text.mentions_to_links(command["text"],
                        command["team_domain"], app.client)
                }
            }
        ])
    else:
        app.client.chat_postEphemeral(
            text="There's nothing for me to send!"
                 " Use `/np <message>` to send a message without pings,"
                 r" and use `@... \` in your message to escape a ping.",
            channel=command["channel_id"],
            user=command["user_id"],
        )
    ...



if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()

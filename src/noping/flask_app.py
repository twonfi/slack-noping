from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request

from noping.__main__ import app

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    # handler runs App's dispatch method
    return handler.handle(request)


if __name__ == "__main__":
    flask_app.run(debug=True)

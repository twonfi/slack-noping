import unittest

from noping.text import *


class TestText(unittest.TestCase):
    def test_mentions_to_links(self):
        self.assertEqual(
            mentions_to_links("hello <@U094NTBR1S5|twonum>!",
                "hackclub"),
            "hello <https://hackclub.slack.com/team/U094NTBR1S5"
                "?noping=1|@twonum>!"
        )
        self.assertEqual(
            mentions_to_links(r"hello <@U094NTBR1S5|twonum>\!",
                "hackclub"),
            r"hello <@U094NTBR1S5|twonum>\!"
        )
        self.assertEqual(
            mentions_to_links(r"hello <@U094NTBR1S5|twonum> \!",
                "hackclub"),
            r"hello <@U094NTBR1S5|twonum> \!"
        )

    def test_user_owns_message(self):
        self.assertTrue(
            user_owns_message("*<@U098A37C0AU>*: hello",
                "U098A37C0AU")
        )
        self.assertFalse(
            user_owns_message("*<@userid2>*: hi",
                "userid1")
        )


    def test_block_kit_mentions_to_links(self):
        self.assertEqual(
            block_kit_mentions_to_links([
                {
                    "text": "Hello, ",
                    "type": "text"
                },
                {
                    "type": "user",
                    "user_id": "U09CE3KJ1FG"
                },
                {
                    "text": "! This is a part of tests of NoPing. ",
                    "type": "text"
                },
                {
                    "type": "user",
                    "user_id": "U095B7T7PFZ"
                },
                {
                    "text": " \\, this is to test \"escaped\" pings, plus ",
                    "type": "text"
                },
                {
                    "type": "user",
                    "user_id": "U19V92D9J9"
                },
                {
                    "text": "\\.",
                    "type": "text"
                },
            ], "workspace"),
            [
                {
                    "text": "Hello, ",
                    "type": "text"
                },
                {
                    "type": "link",
                    "text": "@PlaceholderUsername",
                    "url": f"https://workspace.slack.com"
                           f"/team/U09CE3KJ1FG?noping=1"
                },
                {
                    "text": "! This is a part of tests of NoPing. ",
                    "type": "text"
                },
                {
                    "type": "user",
                    "user_id": "U095B7T7PFZ"
                },
                {
                    "text": " \\, this is to test \"escaped\" pings, plus ",
                    "type": "text"
                },
                {
                    "type": "user",
                    "user_id": "U19V92D9J9"
                },
                {
                    "text": "\\.",
                    "type": "text"
                },
            ]
        )


if __name__ == '__main__':
    unittest.main()

import unittest

from noping.text import *


class TestText(unittest.TestCase):
    def test_mentions_to_links(self):
        self.assertEqual(
            mentions_to_links("hello <@U094NTBR1S5|twonum>!",
                "hackclub"),
            "hello <https://hackclub.slack.com/team/U094NTBR1S5"
                "|@twonum>!"
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
            user_owns_message("*<@U098A37C0AU>* via NoPing: hello",
                "U098A37C0AU")
        )
        self.assertFalse(
            user_owns_message("*<@userid2>* via NoPing: hi",
                "userid1")
        )


if __name__ == '__main__':
    unittest.main()

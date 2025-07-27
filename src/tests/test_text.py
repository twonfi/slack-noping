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


if __name__ == '__main__':
    unittest.main()

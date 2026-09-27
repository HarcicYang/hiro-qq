import unittest

from lagrange.client.server_push.msg import _decode_friend_poke
from lagrange.pb.message.heads import ContentHead, ResponseHead
from lagrange.pb.message.msg import Message
from lagrange.pb.message.msg_push import MsgPushBody
from lagrange.pb.status.friend import GeneralGrayTipInfo, GrayTipTemplateParam


class FriendPokeTest(unittest.TestCase):
    def test_decode_friend_poke(self):
        gray_tip = GeneralGrayTipInfo(
            busi_type=12,
            msg_templ_param=[
                GrayTipTemplateParam(name="uin_str1", value="20002"),
                GrayTipTemplateParam(name="uin_str2", value="10001"),
                GrayTipTemplateParam(name="action_str", value="拍了拍"),
                GrayTipTemplateParam(name="suffix_str", value="一下"),
                GrayTipTemplateParam(name="action_img_url", value="https://example.com/poke.png"),
            ],
        )
        packet = MsgPushBody(
            response_head=ResponseHead(from_uin=20002, from_uid="u_friend", to_uin=10001, to_uid="u_self"),
            content_head=ContentHead(type=0x210, sub_type=290, timestamp=1710000000),
            message=Message(buf2=gray_tip.encode()),
        )

        event = _decode_friend_poke(packet)

        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event.from_uin, 20002)
        self.assertEqual(event.to_uin, 10001)
        self.assertEqual(event.sender_uid, "20002")
        self.assertEqual(event.target_uid, "10001")
        self.assertEqual(event.sender_uin, 20002)
        self.assertEqual(event.target_uin, 10001)
        self.assertEqual(event.action, "拍了拍")
        self.assertEqual(event.suffix, "一下")

    def test_ignore_non_poke_gray_tip(self):
        gray_tip = GeneralGrayTipInfo(busi_type=1)
        packet = MsgPushBody(
            response_head=ResponseHead(from_uin=20002, to_uin=10001),
            content_head=ContentHead(type=0x210, sub_type=290, timestamp=1710000000),
            message=Message(buf2=gray_tip.encode()),
        )

        self.assertIsNone(_decode_friend_poke(packet))


if __name__ == "__main__":
    unittest.main()

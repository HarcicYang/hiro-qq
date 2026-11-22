import json
import re
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING, TypeVar
from urllib.parse import parse_qsl

from lagrange.client.message.decoder import parse_friend_msg, parse_grp_msg
from lagrange.pb.message.msg_push import MsgPush, MsgPushBody
from lagrange.pb.status.friend import GeneralGrayTipInfo, PBFriendRecall, PBFriendRequest
from lagrange.pb.status.group import (
    GroupAdmin,
    GroupRenamedBody,
    GroupSub16Head,
    GroupSub20Head,
    MemberChanged,
    MemberGotTitleBody,
    MemberInviteRequest,
    MemberJoinRequest,
    MemberRecallMsg,
    PBBotGrayTip,
    PBGroupAlbumUpdate,
    PBGroupBotAdded,
    PBGroupInvite,
    PBSelfJoinInGroup,
)
from lagrange.utils.binary.protobuf import ProtoStruct, proto_decode, proto_encode
from lagrange.utils.binary.reader import Reader
from lagrange.utils.operator import timestamp, unpack_dict

from ..events import BaseEvent
from ..events.friend import FriendAddNotify, FriendPoke, FriendRecall, FriendRequest, FriendRequestFinished
from ..events.group import (
    BotGrayTip,
    GroupAdminChange,
    GroupAlbumUpdate,
    GroupBotAdded,
    GroupBotJoined,
    GroupInvite,
    GroupMemberGotSpecialTitle,
    GroupMemberJoinRequest,
    GroupMemberJoined,
    GroupMemberJoinedByInvite,
    GroupMemberQuit,
    GroupMuteMember,
    GroupNameChanged,
    GroupNudge,
    GroupReaction,
    GroupRecall,
    GroupSelfJoined,
    GroupSelfRequireReject,
    GroupSign,
)
from ..wtlogin.sso import SSOPacket
from .log import logger
from .msg_router import msg_push_router

if TYPE_CHECKING:
    from lagrange.client.client import Client

T = TypeVar("T", bound=ProtoStruct)


def _parse_uin(value: str) -> int:
    return int(value) if value.isdigit() else 0


def _payload(pkg: MsgPushBody) -> bytes:
    assert pkg.message is not None and pkg.message.buf2 is not None
    return pkg.message.buf2


def _decode_friend_poke(pkg: MsgPushBody) -> FriendPoke | None:
    if not pkg.message or not pkg.message.buf2:
        return None
    gray_tip = GeneralGrayTipInfo.decode(pkg.message.buf2)
    if not gray_tip or gray_tip.busi_type != 12:
        return None

    params = {param.name: param.value for param in gray_tip.msg_templ_param if param.name}
    sender_uid = params.get("uin_str1", "")
    target_uid = params.get("uin_str2", "")
    if not sender_uid or not target_uid:
        return None

    return FriendPoke(
        from_uin=pkg.response_head.from_uin or 0,
        from_uid=pkg.response_head.from_uid or "",
        to_uin=pkg.response_head.to_uin or 0,
        to_uid=pkg.response_head.to_uid or "",
        timestamp=pkg.content_head.timestamp,
        sender_uid=sender_uid,
        target_uid=target_uid,
        sender_uin=_parse_uin(sender_uid),
        target_uin=_parse_uin(target_uid),
        action=params.get("action_str") or params.get("alt_str1", ""),
        suffix=params.get("suffix_str", ""),
        action_img_url=params.get("action_img_url", ""),
    )


def unpack(buf2: bytes, decoder: type[T]) -> tuple[int, T]:
    reader = Reader(buf2)
    grp_id = reader.read_u32()
    reader.read_u8()
    return grp_id, decoder.decode(reader.read_bytes_with_length("u16", False))


def parse_quoted_str(string: str) -> list[dict[str, str | int]]:
    """
    example data: 'test data <{"cmd": 1, "text": "updated"}> <{"cmd": 2}>!'
    to: [{"cmd": 1, "text": "updated"}, {"cmd": 2}]
    """
    return [json.loads(el) for el in re.findall(r"<(\{.*?})>", string)]


def _parse_group_attrs(pb: GroupSub20Head) -> dict[str, str | int]:
    attrs: dict[str, str | int] = {}
    for item in pb.body.attrs:
        key, value = item.values()
        if isinstance(value, dict):
            value = proto_encode(value)
        if isinstance(value, bytes):
            text = value.decode()
            attrs[key.decode()] = int(text) if text.isdigit() else text
        else:
            attrs[key.decode()] = value
    return attrs


@msg_push_router.on(82, needs_buf2=False)
async def _handle_group_message(client: "Client", pkg: MsgPushBody) -> BaseEvent:
    return await parse_grp_msg(client, pkg)


@msg_push_router.on(166, needs_buf2=False)
@msg_push_router.on(208, needs_buf2=False)
@msg_push_router.on(529, needs_buf2=False)
async def _handle_friend_message(client: "Client", pkg: MsgPushBody) -> BaseEvent:
    return await parse_friend_msg(client, pkg)


@msg_push_router.on(33)
async def _handle_group_member_joined(_: "Client", pkg: MsgPushBody) -> BaseEvent:
    pb = MemberChanged.decode(_payload(pkg))
    return GroupMemberJoined(
        grp_id=pb.uin,
        uid=pb.uid,
        join_type=pb.change_type or 0,
        operator_uid=pb.operator_uid,
    )


@msg_push_router.on(34)
async def _handle_group_member_quit(_: "Client", pkg: MsgPushBody) -> BaseEvent:
    pb = MemberChanged.decode(_payload(pkg))
    return GroupMemberQuit(
        grp_id=pkg.response_head.from_uin or 0,
        uin=pb.uin,
        uid=pb.uid,
        operator_uid=pb.operator_uid,
        exit_type=pb.change_type or 0,
    )


@msg_push_router.on(84)
async def _handle_group_member_join_request(_: "Client", pkg: MsgPushBody) -> BaseEvent:
    pb = MemberJoinRequest.decode(_payload(pkg))
    return GroupMemberJoinRequest(grp_id=pb.grp_id, uid=pb.uid, answer=pb.request_field)


@msg_push_router.on(85)
async def _handle_group_self_joined(_: "Client", pkg: MsgPushBody) -> BaseEvent:
    pb = PBSelfJoinInGroup.decode(_payload(pkg))
    return GroupSelfJoined(grp_id=pb.gid, op_uid=pb.operator_uid)


@msg_push_router.on(86)
async def _handle_group_self_join_rejected(_: "Client", pkg: MsgPushBody) -> BaseEvent:
    reader = Reader(_payload(pkg))
    grp_id = reader.read_u32()
    return GroupSelfRequireReject(grp_id, "")


@msg_push_router.on(87)
async def _handle_group_invite(_: "Client", pkg: MsgPushBody) -> BaseEvent:
    pb = PBGroupInvite.decode(_payload(pkg))
    return GroupInvite(grp_id=pb.gid, invitor_uid=pb.invitor_uid)


@msg_push_router.on(167)
async def _handle_debug_message(_: "Client", pkg: MsgPushBody) -> None:
    assert pkg.message is not None
    logger.debug(pkg.message.encode().hex())


@msg_push_router.on(525)
async def _handle_member_invite_request(_: "Client", pkg: MsgPushBody) -> BaseEvent | None:
    pb = MemberInviteRequest.decode(_payload(pkg))
    if pb.cmd != 87:
        return None
    inner = pb.info.inner
    return GroupMemberJoinRequest(grp_id=inner.grp_id, uid=inner.uid, invitor_uid=inner.invitor_uid)


@msg_push_router.on(44)
async def _handle_group_admin_change(_: "Client", pkg: MsgPushBody) -> BaseEvent:
    pb = GroupAdmin.decode(_payload(pkg))
    admin_body = pb.body.extra_enable if pb.is_set else pb.body.extra_disable
    if admin_body is None:
        raise ValueError(f"Group admin body missing for set={pb.is_set}")
    return GroupAdminChange(grp_id=pb.grp_id, is_set=pb.is_set, uid=admin_body.uid)


@msg_push_router.on(0x210, 35)
async def _handle_friend_request(_: "Client", pkg: MsgPushBody) -> BaseEvent | None:
    pb = PBFriendRequest.decode(_payload(pkg))
    if pb.info:
        return FriendRequest(
            pkg.response_head.from_uin or 0,
            pb.info.from_uid,
            pkg.response_head.to_uin or 0,
            pb.info.to_uid,
            pb.info.verify,
            str(pb.info.source or pb.info.source_new),
        )
    if pb.result:
        return FriendRequestFinished(
            pkg.response_head.from_uin or 0,
            pkg.response_head.from_uid or "",
            pkg.response_head.to_uin or 0,
            pkg.response_head.to_uid or "",
            pb.result.result_code,
        )
    if pb.notify:
        return FriendAddNotify(
            pkg.response_head.from_uin or 0,
            pkg.response_head.from_uid or "",
            pkg.response_head.to_uin or 0,
            pkg.response_head.to_uid or "",
            pb.notify.status,
            pb.notify.timestamp,
            pb.notify.source,
        )
    logger.debug(f"unhandled friend request: {pkg}")
    logger.debug(f"unhandled friend event / group file upload notice event: {pkg}")
    return None


@msg_push_router.on(0x210, 138)
async def _handle_friend_recall(_: "Client", pkg: MsgPushBody) -> BaseEvent:
    pb = PBFriendRecall.decode(_payload(pkg))
    return FriendRecall(
        pkg.response_head.from_uin or 0,
        pb.info.from_uid,
        pkg.response_head.to_uin or 0,
        pb.info.to_uid,
        pb.info.seq,
        pb.info.random,
        pb.info.time,
    )


@msg_push_router.on(0x210, 290)
async def _handle_friend_poke(_: "Client", pkg: MsgPushBody) -> BaseEvent | None:
    return _decode_friend_poke(pkg)


@msg_push_router.on(0x210)
async def _handle_unhandled_friend_event(_: "Client", pkg: MsgPushBody) -> None:
    logger.debug(f"unhandled friend event / group file upload notice event: {pkg}")


@msg_push_router.on(0x2DC, 20)
async def _handle_group_sub20(_: "Client", pkg: MsgPushBody) -> BaseEvent | None:
    grp_id, pb = unpack(_payload(pkg), GroupSub20Head)
    attrs = _parse_group_attrs(pb)
    if pb.body.f2 == 19217:
        return GroupBotJoined(
            grp_id,
            int(attrs["mqq_uin"]),
            str(attrs["nick_name"]),
            str(attrs["robot_name"]),
            str(attrs["robot_schema"]),
            str(attrs["user_schema"]),
        )
    if pb.body.type == 1:
        if "invitor" in attrs:
            invitee = attrs.get("invitee")
            if invitee is None:
                invitee = int(ET.fromstring(str(attrs["invitees_dynamic"])).attrib["uin"])
            return GroupMemberJoinedByInvite(grp_id, int(attrs["invitor"]), int(invitee))
        if "user" in attrs and "uin" in attrs:
            return None
        raise TypeError(f"Unhandled GrayTips with attribute: {attrs}")
    if pb.body.type == 12:
        return GroupNudge(
            grp_id,
            int(attrs["uin_str1"]),
            int(attrs["uin_str2"]),
            str(attrs["action_str"] if "action_str" in attrs else attrs["alt_str1"]),
            str(attrs["suffix_str"]),
            attrs,
            pb.body.attrs_xml,
        )
    if pb.body.type == 14:
        return GroupSign(
            grp_id,
            int(attrs["mqq_uin"]),
            str(attrs["mqq_nick"]),
            timestamp(),
            attrs,
            pb.body.attrs_xml,
        )
    raise ValueError(f"unknown type({pb.body.type}) f2({pb.body.f2}) on GroupSub20: {attrs}")


@msg_push_router.on(0x2DC, 16)
async def _handle_group_sub16(_client: "Client", pkg: MsgPushBody) -> BaseEvent | None:
    buf2 = _payload(pkg)
    grp_id, pb = unpack(buf2, GroupSub16Head)
    if pb.flag is None:
        _, bot = unpack(buf2, PBBotGrayTip)
        return BotGrayTip(grp_id, bot.body.message)
    if pb.flag == 6:
        if pb.body is None:
            raise ValueError("special title body missing")
        body = MemberGotTitleBody.decode(pb.body)
        detail = next((item for item in parse_quoted_str(body.string) if item["cmd"] == 1), None)
        if detail is None:
            raise ValueError("cannot find special_title and url")
        return GroupMemberGotSpecialTitle(
            grp_id=grp_id,
            member_uin=body.member_uin,
            special_title=str(detail["text"]),
            _detail_url=str(detail["data"]),
        )
    if pb.flag == 12:
        if pb.body is None:
            raise ValueError("renamed group body missing")
        body = GroupRenamedBody.decode(pb.body)
        return GroupNameChanged(
            grp_id=grp_id,
            name_new=body.grp_name,
            timestamp=pb.timestamp,
            operator_uid=pb.operator_uid,
        )
    if pb.flag == 35:
        if pb.f44 is None:
            raise ValueError("group reaction body missing")
        body = pb.f44.inner.body
        return GroupReaction(
            grp_id=grp_id,
            uid=body.detail.sender_uid,
            seq=body.msg.id,
            emoji_id=int(body.detail.emo_id),
            emoji_type=body.detail.emo_type,
            emoji_count=body.detail.count,
            type=body.detail.send_type,
            total_operations=body.msg.total_operations,
        )
    if pb.flag in (21, 23):
        return None
    if pb.flag == 37:
        _, album = unpack(buf2, PBGroupAlbumUpdate)
        query = dict(parse_qsl(album.body.args))
        return GroupAlbumUpdate(
            grp_id=album.grp_id,
            timestamp=album.timestamp,
            image_id=query["i"],
        )
    if pb.flag == 38:
        _, bot = unpack(buf2, PBGroupBotAdded)
        bot_uid = bot.body.bot_uid_1 or bot.body.bot_uid_2
        if bot_uid is None:
            raise ValueError("group bot uid missing")
        return GroupBotAdded(bot.body.grp_id, bot_uid)
    raise ValueError(f"Unknown subtype_12 flag: {pb.flag}: {pb.body.hex() if pb.body else pb}")


@msg_push_router.on(0x2DC, 17)
async def _handle_group_recall(_: "Client", pkg: MsgPushBody) -> BaseEvent:
    grp_id, pb = unpack(_payload(pkg), MemberRecallMsg)
    info = pb.body.info
    return GroupRecall(
        uid=info.uid,
        seq=info.seq,
        time=info.time,
        rand=info.rand,
        grp_id=grp_id,
        operator_id=pb.body.uid,
        suffix=pb.body.extra.suffix.strip() if pb.body.extra else "",
    )


@msg_push_router.on(0x2DC, 12)
async def _handle_group_mute(_: "Client", pkg: MsgPushBody) -> BaseEvent:
    info = proto_decode(_payload(pkg))
    return GroupMuteMember(
        grp_id=info.into(1, int),
        operator_uid=info.into(4, bytes).decode(),
        target_uid=unpack_dict(info.proto, "5.3.1", b"").decode(),
        duration=unpack_dict(info.proto, "5.3.2"),
    )


@msg_push_router.on(0x2DC, 1)
@msg_push_router.on(0x2DC, 21)
async def _handle_ignored_group_event(_: "Client", __: MsgPushBody) -> None:
    return None


@msg_push_router.on(0x2DC)
async def _handle_unhandled_group_event(_: "Client", pkg: MsgPushBody) -> None:
    payload = _payload(pkg)
    logger.debug(f"unknown sub_type {pkg.content_head.sub_type}: {payload.hex() if payload else pkg}")


async def msg_push_handler(client: "Client", sso: SSOPacket) -> BaseEvent | None:
    return await msg_push_router.dispatch(client, MsgPush.decode(sso.data).body)

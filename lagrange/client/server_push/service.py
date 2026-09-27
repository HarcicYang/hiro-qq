import os
import datetime

from lagrange.pb.status.kick import KickNT
from lagrange.pb.login.register import PBSsoInfoSyncPush, PBServerPushParams

from ..events.service import ServerKick, OtherClientInfo
from ..wtlogin.sso import SSOPacket
from .log import logger

DBG_EN = bool(os.environ.get("PUSH_DEBUG", False))


async def server_kick_handler(_, sso: SSOPacket):
    ev = KickNT.decode(sso.data)
    return ServerKick(tips=ev.tips, title=ev.title)


async def server_info_sync_handler(_, sso: SSOPacket):
    if not DBG_EN:
        return
    ev = PBSsoInfoSyncPush.decode(sso.data)
    if ev.cmd_type == 5:  # grp info
        logger.debug("GroupInfo Sync:")
        for i in ev.grp_info:
            timestamp = datetime.datetime.fromtimestamp(i.last_msg_timestamp).strftime("%Y-%m-%d %H:%M:%S")
            logger.debug(
                f"{i.grp_id}({i.grp_name}): lostsync: {i.last_msg_seq - i.last_msg_seq_read}, time: {timestamp}"
            )
    elif ev.cmd_type == 2:
        logger.debug("MsgPush Sync:")
        for i in ev.grp_msgs.inner:
            timestamp = datetime.datetime.fromtimestamp(i.last_msg_time).strftime("%Y-%m-%d %H:%M:%S")
            logger.debug(f"{len(i.msgs)} msgs({i.start_seq}->{i.end_seq}) in {i.grp_id}, time: {timestamp}")
        logger.debug("EventPush Sync:")
        for i in ev.sys_events.inner:
            timestamp = datetime.datetime.fromtimestamp(i.last_evt_time).strftime("%Y-%m-%d %H:%M:%S")
            logger.debug(f"{len(i.events)} events in {i.grp_id}, time: {timestamp}")
    else:
        logger.debug(f"Unknown cmd_type: {ev.cmd_type}({ev.f4})")
    logger.debug("END")


async def server_push_param_handler(_, sso: SSOPacket):
    ev = PBServerPushParams.decode(sso.data)
    return OtherClientInfo(
        [OtherClientInfo.ClientOnline(i.sub_id, i.os_name, i.device_name) for i in ev.online_devices]
    )


async def server_push_req_handler(_, sso: SSOPacket):
    """
    JCE packet, ignore
    """
    return None

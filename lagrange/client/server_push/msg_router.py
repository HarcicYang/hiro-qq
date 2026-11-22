from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeAlias

from lagrange.client.events import BaseEvent
from lagrange.pb.message.msg_push import MsgPushBody

from .log import logger

if TYPE_CHECKING:
    from lagrange.client.client import Client

MsgPushKey: TypeAlias = tuple[int, int | None]
MsgPushHandler: TypeAlias = Callable[["Client", MsgPushBody], Awaitable[BaseEvent | None]]


@dataclass(frozen=True, slots=True)
class MsgPushRoute:
    handler: MsgPushHandler
    needs_buf2: bool = True


class MsgPushRouter:
    def __init__(self) -> None:
        self._routes: dict[MsgPushKey, MsgPushRoute] = {}

    def on(
        self,
        typ: int,
        sub_type: int | None = None,
        *,
        needs_buf2: bool = True,
    ) -> Callable[[MsgPushHandler], MsgPushHandler]:
        def register(handler: MsgPushHandler) -> MsgPushHandler:
            key = (typ, sub_type)
            if key in self._routes:
                raise ValueError(f"duplicate MsgPush route: {key}")
            self._routes[key] = MsgPushRoute(handler, needs_buf2)
            return handler

        return register

    async def dispatch(self, client: "Client", pkg: MsgPushBody) -> BaseEvent | None:
        typ = pkg.content_head.type
        raw_sub_type = pkg.content_head.sub_type
        sub_type = -1 if raw_sub_type is None else raw_sub_type
        logger.debug(f"msg_push received, type: {typ}.{sub_type}")

        if pkg.message is None:
            logger.debug(f"msg_push has no message body: {pkg}")
            return None

        route = self._routes.get((typ, sub_type)) or self._routes.get((typ, None))
        if route is None:
            if pkg.message.buf2 is None:
                logger.debug(f"msg_push has no protobuf payload: {pkg}")
                return None
            payload = pkg.message.buf2.hex() if pkg.message.buf2 else pkg
            logger.debug(f"unknown type {typ}, sub type {sub_type}: {payload}")
            return None

        if route.needs_buf2 and pkg.message.buf2 is None:
            logger.debug(f"msg_push has no protobuf payload: {pkg}")
            return None

        return await route.handler(client, pkg)


msg_push_router = MsgPushRouter()

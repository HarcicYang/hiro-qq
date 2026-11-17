import json

from lagrange.info import AppInfo
from typing import Literal
from collections.abc import Callable, Awaitable
import asyncio

from .client.client import Client as Client

# from .client.server_push.msg import msg_push_handler
# from .client.server_push.service import server_kick_handler
from .utils.log import log as log
from .utils.log import install_loguru as install_loguru
from .utils.sign import fetch_appinfo, sign_provider, sign_provider_android
from .info import InfoManager
from .info.app import app_list
from .utils.binary.protobuf.models import evaluate_all


class Lagrange:
    client: Client

    def __init__(
        self,
        uin: int,
        protocol: Literal["linux", "macos", "windows", "android_phone", "android_pad", "custom"] = "linux",
        sign_url: str | None = None,
        device_info_path: str = "./device.json",
        signinfo_path: str = "./sig.bin",
        custom_protocol_path: str = "./protocol.json",
        use_ipv6: bool = True,
        use_optimum: bool = False,
        fetch_appinfo: bool = False,
        custom_sign_provider: Callable[[int, str, str, str], Callable[[str, int, bytes], Awaitable[dict | None]]]
        | None = None,
    ):
        self.im = InfoManager(uin, device_info_path, signinfo_path)
        self.uin = uin
        self._sign_url = sign_url
        self._custom_sign_provider = custom_sign_provider
        self.sign = None
        self.events = {}
        self.log = log
        self._protocol = protocol
        self._protocol_path = custom_protocol_path
        self.use_ipv6 = use_ipv6
        self.use_optimum = use_optimum
        self._fetch_appinfo = fetch_appinfo

    def subscribe(self, event, handler):
        self.events[event] = handler

    async def login(self, client: Client):
        if self.im.sig_info.d2:
            if not await client.register():
                return await client.login()
            return True
        else:
            return await client.login()

    async def run(self):
        if self._protocol == "custom":
            log.root.debug(f"load custom protocol from {self._protocol_path}")
            with open(self._protocol_path) as f:
                proto = json.loads(f.read())
            app_info = AppInfo.load_custom(proto)
        else:
            app_info = app_list[self._protocol]
        if self._fetch_appinfo and self._sign_url:
            remote_app_info = await fetch_appinfo(self._sign_url)
            if remote_app_info:
                app_info = remote_app_info
                log.root.info("AppInfo: fetched from sign server")
            else:
                log.root.warning("AppInfo: fetch from sign server failed, using builtin")
        log.root.info(f"AppInfo: platform={app_info.os}, ver={app_info.build_version}({app_info.sub_app_id})")

        with self.im as im:
            if self._custom_sign_provider:
                self.sign = self._custom_sign_provider(
                    self._sign_url,  # type: ignore
                    self.uin,  # type: ignore
                    im.device.guid,
                    app_info.qua,
                )
            elif self._sign_url:
                if app_info.os.casefold() == "android":
                    self.sign = sign_provider_android(
                        self._sign_url,
                        self.uin,
                        im.device.guid,
                        app_info.qua,
                        app_info.pt_version,
                        app_info.wtlogin_sdk,
                    )
                else:
                    self.sign = sign_provider(
                        self._sign_url,
                        self.uin,
                        im.device.guid,
                        app_info.qua,
                    )
            else:
                log.root.warning("none of custom_sign_provider or sign_url provided, continue with no sign")
            self.client = Client(self.uin, app_info, im.device, im.sig_info, self.sign, self.use_ipv6, self.use_optimum)
            for event, handler in self.events.items():
                self.client.events.subscribe(event, handler)
            self.client.connect()
            status = await self.login(self.client)
        if not status:
            log.login.error("Login failed")
            return
        await self.client.wait_closed()

    def launch(self):
        try:
            asyncio.run(self.run())
        except KeyboardInterrupt:
            self.client._task_clear()
            log.root.info("Program exited by user")
        else:
            log.root.info("Program exited normally")


evaluate_all()

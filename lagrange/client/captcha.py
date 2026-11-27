import asyncio
import json
from urllib import parse

from qrcode.main import QRCode

from lagrange.utils.httpcat import HttpCat
from lagrange.utils.log import log


class OnlineCaptchaResolver:
    def __init__(self, service: str, uin: int, interval: float = 1.0):
        self._service = service.rstrip("/")
        self._uin = uin
        self._interval = interval

    def build_captcha_url(self, url: str) -> str:
        query = parse.urlparse(url).query.replace("uin=0", f"uin={self._uin}")
        return f"{self._service}/captcha?{query}"

    async def __call__(self, url: str) -> tuple[str, str]:
        captcha_url = self.build_captcha_url(url)
        log.login.warning(f"please solve captcha at: {captcha_url}")
        qr = QRCode()
        qr.add_data(captcha_url)
        qr.print_ascii()

        query_url = f"{self._service}/get_captcha?uin={self._uin}"
        while True:
            rsp = await HttpCat.request("GET", query_url, conn_timeout=10)
            if rsp.code == 404:
                await asyncio.sleep(self._interval)
                continue
            data = json.loads(rsp.decompressed_body).get("data")
            if not isinstance(data, str) or "|" not in data:
                await asyncio.sleep(self._interval)
                continue
            ticket, rand_str = data.split("|", 1)
            log.login.info("captcha solved")
            return ticket, rand_str

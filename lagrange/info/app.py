import re
from dataclasses import dataclass
from typing import Any, TypedDict, cast

from .serialize import JsonSerializer


_trans_map = {
    "SsoVersion": "pt_os_version",
    "WtLoginSdk": "wtlogin_sdk",
    "AppIdQrCode": "app_id_qrcode",
    "MainSigMap": "main_sigmap",
    "SubSigMap": "sub_sigmap",
}


def _translate_appinfo(s: dict[str, int | str]) -> dict[str, int | str]:
    out: dict[str, int | str] = {}
    for k, v in s.items():
        if k in _trans_map:
            out[_trans_map[k]] = v
        else:
            k = re.sub(r"([A-Z])([^A-Z]+)", r"_\1\2", k).lstrip("_").lower()
            out[k] = v
    return out


@dataclass
class AppInfo(JsonSerializer):
    os: str
    kernel: str
    vendor_os: str

    current_version: str
    # build_version: int
    misc_bitmap: int
    pt_version: str
    pt_os_version: int
    package_name: str
    wtlogin_sdk: str
    app_id: int
    sub_app_id: int
    app_id_qrcode: int
    app_client_version: int
    main_sigmap: int
    sub_sigmap: int
    nt_login_type: int
    qua: str = ""

    @property
    def build_version(self) -> int:
        parts = self.current_version.split("-")
        return int(parts[1]) if len(parts) > 1 else self.app_client_version

    @property
    def package_sign(self) -> str:
        # QUA?
        if self.os == "Windows":
            kernel = "WIN"
        elif self.os == "Linux":
            kernel = "LNX"
        elif self.os == "Mac":
            kernel = "MAC"
        else:
            raise NotImplementedError(self.os)
        return f"V1_{kernel}_NQ_{self.current_version}_RDM_B"

    @classmethod
    def load_custom(cls, d: dict[str, int | str]) -> "AppInfo":
        return cls(**cast(Any, _translate_appinfo(d)))


class AppInfoDict(TypedDict):
    linux: AppInfo
    macos: AppInfo
    windows: AppInfo
    android_phone: AppInfo
    android_pad: AppInfo


app_list: AppInfoDict = {
    "linux": AppInfo(
        os="Linux",
        kernel="Linux",
        vendor_os="linux",
        current_version="3.2.26-46494",
        misc_bitmap=32764,
        pt_version="2.0.0",
        pt_os_version=19,
        package_name="com.tencent.qq",
        wtlogin_sdk="nt.wtlogin.0.0.1",
        app_id=1600001615,
        sub_app_id=537345891,
        app_id_qrcode=13697054,
        app_client_version=46494,
        main_sigmap=169742560,
        sub_sigmap=0,
        nt_login_type=1,
        qua="V1_LNX_NQ_3.2.26_46494_GW_B",
    ),
    "macos": AppInfo(
        os="Mac",
        kernel="Darwin",
        vendor_os="mac",
        current_version="6.9.23-20139",
        misc_bitmap=12058620,
        pt_version="2.0.0",
        pt_os_version=23,
        package_name="com.tencent.qq",
        wtlogin_sdk="nt.wtlogin.0.0.1",
        app_id=1600001602,
        sub_app_id=537200848,
        app_id_qrcode=537162356,
        app_client_version=13172,
        main_sigmap=169732560,
        sub_sigmap=0,
        nt_login_type=5,
        qua="",
    ),
    "windows": AppInfo(
        os="Windows",
        kernel="Windows_NT",
        vendor_os="win32",
        current_version="9.9.19-35184",
        pt_version="2.0.0",
        misc_bitmap=12058620,
        pt_os_version=23,
        package_name="com.tencent.qq",
        wtlogin_sdk="nt.wtlogin.0.0.1",
        app_id=1600001604,
        sub_app_id=537291048,
        app_id_qrcode=537138217,
        app_client_version=35184,
        main_sigmap=169732560,
        sub_sigmap=0,
        nt_login_type=5,
        qua="",
    ),
    "android_phone": AppInfo(
        os="Android",
        kernel="Linux",
        vendor_os="android",
        current_version="9.1.60.045f5d19",
        misc_bitmap=150470524,
        pt_version="9.1.60",
        pt_os_version=22,
        package_name="com.tencent.mobileqq",
        wtlogin_sdk="6.0.0.2568",
        app_id=16,
        sub_app_id=537275636,
        app_id_qrcode=16,
        app_client_version=0,
        main_sigmap=16724722,
        sub_sigmap=66560,
        nt_login_type=1,
        qua="V1_AND_SQ_9.1.60_9388_YYB_D",
    ),
    "android_pad": AppInfo(
        os="ANDROID",
        kernel="Linux",
        vendor_os="android",
        current_version="9.3.70.41925",
        misc_bitmap=150470524,
        pt_version="9.3.70",
        pt_os_version=22,
        package_name="com.tencent.mobileqq",
        wtlogin_sdk="6.0.0.2591",
        app_id=16,
        sub_app_id=537395477,
        app_id_qrcode=16,
        app_client_version=0,
        main_sigmap=16724722,
        sub_sigmap=66560,
        nt_login_type=1,
        qua="V1_AND_SQ_9.3.70_16410_YYB_D",
    ),
}

import os
from hashlib import md5, sha256

from lagrange.client.packet import PacketBuilder
from lagrange.info import AppInfo, DeviceInfo
from lagrange.utils.binary.protobuf import proto_encode
from lagrange.utils.crypto.tea import qqtea_encrypt
from lagrange.utils.operator import timestamp

from .common import CommonTlvBuilder

ANDROID_APK_SIGNATURE = bytes.fromhex("A6B745BF24A2C277527716F6F36EB68D")

_DEVICE_REPORT_TEMPLATE = {
    1: "V816.0.6.0.TKHCNXM",
    2: (
        "Linux version 4.19.157-perf-g92c089fc2d37 (builder@pangu-build-component-vendor-272092-qncbv-vttl3-61r9m) "
        "(clang version 10.0.7 for Android NDK, GNU ld (binutils-2.27-bd24d23f) 2.27.0.20170315) "
        "#1 SMP PREEMPT Wed Jun 5 13:27:08 UTC 2024"
    ),
    3: "REL",
    5: "Redmi/alioth/alioth:13/TKQ1.221114.001/V816.0.6.0.TKHCNXM:user/release-keys",
    6: "unknown",
    8: "",
    9: "V816.0.6.0.TKHCNXM",
}

_ACC_DOMAINS = [
    "office.qq.com",
    "qun.qq.com",
    "gamecenter.qq.com",
    "docs.qq.com",
    "mail.qq.com",
    "tim.qq.com",
    "ti.qq.com",
    "vip.qq.com",
    "tenpay.com",
    "qqweb.qq.com",
    "qzone.qq.com",
    "mma.qq.com",
    "game.qq.com",
    "openmobile.qq.com",
    "connect.qq.com",
]


def generate_tlv548() -> bytes:
    src = bytearray(os.urandom(128))
    src[0] = 21

    src_num = int.from_bytes(src, "big")
    dst_num = src_num + 10000
    dst = dst_num.to_bytes((dst_num.bit_length() + 7) // 8, "big")
    tgt = sha256(dst).digest()

    inner = (
        PacketBuilder()
        .write_u8(1)
        .write_u8(2)
        .write_u8(1)
        .write_u8(2)
        .write_u16(10)
        .write_bytes(bytes(2))
        .write_bytes(bytes(src), "u16", False)
        .write_bytes(tgt, "u16", False)
    ).pack()

    return (
        PacketBuilder()
        .write_u8(1)
        .write_u8(2)
        .write_u8(1)
        .write_u8(1)
        .write_u16(10)
        .write_bytes(bytes(2))
        .write_bytes(bytes(src), "u16", False)
        .write_bytes(tgt, "u16", False)
        .write_bytes(inner, "u16", False)
        .write_bytes(dst, "u16", False)
        .write_u32(0)
        .write_u32(10000)
    ).pack()


class AndroidTlvBuilder(CommonTlvBuilder):
    @classmethod
    def t1(cls, uin: int) -> bytes:
        return (
            cls()
            .write_i16(1)
            .write_u32(int.from_bytes(os.urandom(4), "big"))
            .write_u32(uin)
            .write_u32(timestamp())
            .write_u32(0)
            .write_i16(0)
        ).pack(0x1)

    @classmethod
    def t8(cls) -> bytes:
        return cls().write_u16(0).write_u32(2052).write_u16(0).pack(0x8)

    @classmethod
    def t18_android(cls, app_info: AppInfo, uin: int) -> bytes:
        return (
            cls()
            .write_i16(1)
            .write_u32(0x600)
            .write_u32(app_info.app_id)
            .write_i32(app_info.app_client_version)
            .write_u32(uin)
            .write_i16(0)
            .write_i16(0)
        ).pack(0x18)

    @classmethod
    def t100_android(cls, app_info: AppInfo, main_sigmap: int) -> bytes:
        return (
            cls()
            .write_u16(1)
            .write_u32(app_info.pt_os_version)
            .write_u32(app_info.app_id)
            .write_u32(app_info.sub_app_id)
            .write_i32(app_info.app_client_version)
            .write_u32(main_sigmap)
        ).pack(0x100)

    @classmethod
    def t106_android(
        cls,
        app_info: AppInfo,
        uin: int,
        password_md5: bytes,
        guid: bytes,
        tgtgt_key: bytes,
    ) -> bytes:
        key = md5(password_md5 + bytes(4) + int(uin).to_bytes(4, "big")).digest()
        body = (
            cls()
            .write_i16(4)
            .write_u32(int.from_bytes(os.urandom(4), "big"))
            .write_u32(app_info.pt_os_version)
            .write_u32(app_info.app_id)
            .write_i32(app_info.app_client_version)
            .write_u32(uin)
            .write_u32(timestamp())
            .write_u32(0)
            .write_u8(1)
            .write_bytes(password_md5)
            .write_bytes(tgtgt_key)
            .write_u32(0)
            .write_u8(1)
            .write_bytes(guid)
            .write_u32(app_info.sub_app_id)
            .write_u32(1)
            .write_string(str(uin), "u16", False)
            .write_i16(0)
        ).data
        return cls().write_bytes(qqtea_encrypt(body, key), "u32", False).pack(0x106)

    @classmethod
    def t107_android(cls) -> bytes:
        return cls().write_u16(0).write_u8(0).write_u16(0).write_u8(1).pack(0x107)

    @classmethod
    def t109(cls, android_id: str) -> bytes:
        return cls().write_bytes(md5(android_id.encode()).digest()).pack(0x109)

    @classmethod
    def t124_android(cls) -> bytes:
        return (
            cls()
            .write_string("android", "u16", False)
            .write_string("13", "u16", False)
            .write_i16(2)
            .write_string("", "u16", False)
            .write_string("wifi", "u32", False)
        ).pack(0x124)

    @classmethod
    def t141_android(cls) -> bytes:
        return (
            cls()
            .write_u16(1)
            .write_string("", "u16", False)
            .write_string("", "u16", False)
            .write_string("wifi", "u16", False)
        ).pack(0x141)

    @classmethod
    def t144_report(cls, app_info: AppInfo, device: DeviceInfo, tgtgt_key: bytes, android_id: str) -> bytes:
        report = dict(_DEVICE_REPORT_TEMPLATE)
        report[7] = android_id
        inner = (
            cls()
            .write_bytes(cls.t109(android_id))
            .write_bytes(cls.t52d(report))
            .write_bytes(cls.t124_android())
            .write_bytes(cls.t128(app_info.os, bytes.fromhex(device.guid)))
            .write_bytes(cls.t16e(device.device_name))
        )
        return PacketBuilder(tgtgt_key).write_bytes(inner.data).pack(0x144)

    @classmethod
    def t147_android(cls, app_info: AppInfo) -> bytes:
        return (
            cls()
            .write_u32(app_info.app_id)
            .write_string(app_info.pt_version, "u16", False)
            .write_bytes(app_info.apk_signature_md5 or ANDROID_APK_SIGNATURE, "u16", False)
        ).pack(0x147)

    @classmethod
    def t154(cls) -> bytes:
        return cls().write_u32(0).pack(0x154)

    @classmethod
    def t177_android(cls, sdk_version: str) -> bytes:
        return cls().write_u8(1).write_u32(0).write_string(sdk_version, "u16", False).pack(0x177)

    @classmethod
    def t187(cls) -> bytes:
        return cls().write_bytes(md5(bytes.fromhex("020000000000")).digest()).pack(0x187)

    @classmethod
    def t188(cls, android_id: str) -> bytes:
        return cls().write_bytes(md5(android_id.encode()).digest()).pack(0x188)

    @classmethod
    def t511(cls) -> bytes:
        builder = cls().write_i16(len(_ACC_DOMAINS))
        for domain in _ACC_DOMAINS:
            builder.write_u8(1).write_string(domain, "u16", False)
        return builder.pack(0x511)

    @classmethod
    def t516(cls) -> bytes:
        return cls().write_u32(0).pack(0x516)

    @classmethod
    def t521_android(cls) -> bytes:
        return cls().write_u32(0).write_string("", "u16", False).pack(0x521)

    @classmethod
    def t525(cls) -> bytes:
        return cls().write_i16(1).write_i16(0x536).write_bytes(bytes.fromhex("020100"), "u16", False).pack(0x525)

    @classmethod
    def t52d(cls, report: dict[int, str]) -> bytes:
        return cls().write_bytes(proto_encode(report)).pack(0x52D)

    @classmethod
    def t544(cls, energy: bytes) -> bytes:
        return cls().write_bytes(energy).pack(0x544)

    @classmethod
    def t545(cls, qimei: str) -> bytes:
        return cls().write_bytes(qimei.encode()).pack(0x545)

    @classmethod
    def t547(cls, client_pow: bytes) -> bytes:
        return cls().write_bytes(client_pow).pack(0x547)

    @classmethod
    def t548(cls, native_test_data: bytes) -> bytes:
        return cls().write_bytes(native_test_data).pack(0x548)

    @classmethod
    def t553(cls, attach: bytes) -> bytes:
        return cls().write_bytes(attach).pack(0x553)

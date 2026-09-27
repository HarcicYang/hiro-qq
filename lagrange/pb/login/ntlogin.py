from lagrange.utils.binary.protobuf import ProtoStruct, proto_field


class _LoginCookies(ProtoStruct, debug=True):
    str: str = proto_field(1)  # type: ignore


class _LoginVerify(ProtoStruct, debug=True):
    url: str = proto_field(3)


class _LoginErrField(ProtoStruct, debug=True):
    code: int = proto_field(1)
    title: str = proto_field(2)
    message: str = proto_field(3)


class _LoginRspHead(ProtoStruct, debug=True):
    account: dict = proto_field(1)  # {1: uin}
    device: dict = proto_field(2)  # {1: app.os, 2: device_name, 3: nt_login_type, 4: bytes(guid)}
    system: dict = proto_field(3)  # {1: device.kernel_version, 2: app.app_id, 3: app.package_name}
    error: _LoginErrField | None = proto_field(4, default=None)
    cookies: _LoginCookies | None = proto_field(5, default=None)


class _LoginCredentials(ProtoStruct, debug=True):
    credentials: bytes | None = proto_field(1, default=None)  # on login request
    temp_pwd: bytes | None = proto_field(3, default=None)
    tgt: bytes | None = proto_field(4, default=None)
    d2: bytes | None = proto_field(5, default=None)
    d2_key: bytes | None = proto_field(6, default=None)


class _LoginRspBody(ProtoStruct, debug=True):
    credentials: _LoginCredentials | None = proto_field(1, default=None)
    verify: _LoginVerify | None = proto_field(2, default=None)


class NTLoginRsp(ProtoStruct, debug=True):
    head: _LoginRspHead = proto_field(1)
    body: _LoginRspBody | None = proto_field(2, default=None)

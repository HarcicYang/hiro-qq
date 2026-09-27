from lagrange.utils.binary.protobuf import proto_field, ProtoStruct

from .rich_text import RichText


class Message(ProtoStruct):
    body: RichText | None = proto_field(1, default=None)
    buf2: bytes | None = proto_field(2, default=None)
    buf3: bytes | None = proto_field(3, default=None)

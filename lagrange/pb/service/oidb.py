from lagrange.utils.binary.protobuf import proto_field, ProtoStruct


class OidbRequest(ProtoStruct):
    cmd: int = proto_field(1)
    sub_cmd: int = proto_field(2)
    data: bytes = proto_field(4)
    reserved: int = proto_field(12, default=0)


class OidbResponse(OidbRequest):
    ret_code: int = proto_field(3)
    err_msg: str = proto_field(5)

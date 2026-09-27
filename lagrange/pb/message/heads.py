from lagrange.utils.binary.protobuf import proto_field, ProtoStruct


class Forward(ProtoStruct):
    f1: int = proto_field(1, default=0)
    f2: int = proto_field(2, default=0)
    f3: int = proto_field(3, default=0)
    custom_flag: bytes = proto_field(4, default=b"")  # 好弱智，不设置不显示自定义名字和头像
    avatar_url: str = proto_field(5, default="")  # input costom url


class ContentHead(ProtoStruct):
    type: int = proto_field(1)
    sub_type: int | None = proto_field(2, default=None)  # when send ,private is 175, group is None
    f3: int | None = proto_field(3, default=None)  # In forward msg, this field like sub_type
    random: int = proto_field(4, default=0)
    seq: int = proto_field(5, default=0)
    timestamp: int = proto_field(6, default=0)
    pkg_num: int = proto_field(7, default=1)
    pkg_index: int = proto_field(8, default=0)
    div_seq: int = proto_field(9, default=0)
    c2c_seq: int | None = proto_field(11, default=None)
    # new_id: int = proto_field(12)
    forward: Forward | None = proto_field(15, default=None)


class Grp(ProtoStruct):
    gid: int = proto_field(1, default=0)
    sender_name: str = proto_field(4, default="")  # empty in get_grp_msg
    f5: int | None = proto_field(5, default=None)
    grp_name: str | None = proto_field(7, default=None)


class ResponseHead(ProtoStruct):
    from_uin: int | None = proto_field(1, default=None)
    from_uid: str | None = proto_field(2, default=None)
    type: int | None = proto_field(3, default=None)
    sigmap: int | None = proto_field(4, default=None)
    to_uin: int | None = proto_field(5, default=None)
    to_uid: str | None = proto_field(6, default=None)
    rsp_grp: Grp | None = proto_field(8, default=None)

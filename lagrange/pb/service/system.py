from lagrange.utils.binary.protobuf import ProtoStruct, proto_field


class ProfileStringProperty(ProtoStruct):
    key: int = proto_field(1)
    value: bytes = proto_field(2)


class ProfileNumberProperty(ProtoStruct):
    key: int = proto_field(1)
    value: int = proto_field(2)


class ModifySelfProfileReq(ProtoStruct):
    uin: int = proto_field(1)
    string_props: list[ProfileStringProperty] = proto_field(2, default_factory=list)
    number_props: list[ProfileNumberProperty] = proto_field(3, default_factory=list)

    @classmethod
    def build(
        cls,
        uin: int,
        *,
        string_props: dict[int, bytes] | None = None,
        number_props: dict[int, int] | None = None,
    ) -> "ModifySelfProfileReq":
        return cls(
            uin=uin,
            string_props=[ProfileStringProperty(key=key, value=value) for key, value in (string_props or {}).items()],
            number_props=[ProfileNumberProperty(key=key, value=value) for key, value in (number_props or {}).items()],
        )

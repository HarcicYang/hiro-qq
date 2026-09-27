from lagrange.utils.binary.protobuf import proto_field, ProtoStruct

from .elems import (
    CommonElem,
    CustomFace,
    ExtraInfo,
    Face,
    MarketFace,
    MiniApp,
    NotOnlineImage,
    OnlineImage,
    OpenData,
    Ptt,
    RichMsg,
    SrcMsg,
    Text,
    TransElem,
    VideoFile,
    GeneralFlags,
)

__all__ = ["Elems", "RichText"]


class Elems(ProtoStruct, debug=True):
    text: Text | None = proto_field(1, default=None)
    face: Face | None = proto_field(2, default=None)
    online_image: OnlineImage | None = proto_field(3, default=None)
    not_online_image: NotOnlineImage | None = proto_field(4, default=None)
    trans_elem: TransElem | None = proto_field(5, default=None)
    market_face: MarketFace | None = proto_field(6, default=None)
    custom_face: CustomFace | None = proto_field(8, default=None)
    elem_flags2: bytes | None = proto_field(9, default=None)
    rich_msg: RichMsg | None = proto_field(12, default=None)
    extra_info: ExtraInfo | None = proto_field(16, default=None)
    video_file: VideoFile | None = proto_field(19, default=None)
    general_flags: GeneralFlags | None = proto_field(37, default=None)
    open_data: OpenData | None = proto_field(41, default=None)
    src_msg: SrcMsg | None = proto_field(45, default=None)
    mini_app: MiniApp | None = proto_field(51, default=None)
    common_elem: CommonElem | None = proto_field(53, default=None)


class RichText(ProtoStruct):
    attrs: dict | None = proto_field(1, default=None)
    content: list[Elems] = proto_field(2)
    not_online_file: dict | None = proto_field(3, default=None)
    ptt: Ptt | None = proto_field(4, default=None)

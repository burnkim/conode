# GENERATED — 편집 금지. 원천: packages/schema/protocol.schema.json
# 재생성: pnpm --filter @conode/schema generate
from __future__ import annotations

from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

PROTOCOL_VERSION = 0

ParamValue = Union[bool, int, float, str, list[float]]

Category = Literal["input", "vision", "depth", "generate", "audio", "output"]

class NodeInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    name: str
    category: Category
    index: int
    node_type: Optional[str] = None
    inputs: Optional[list[str]] = None
    params: Optional[dict] = None

class Edge(BaseModel):
    model_config = ConfigDict(extra="forbid")
    src: str
    dst: str
    port: str

class Hello(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["hello"] = "hello"
    v: Literal[0] = 0
    role: Literal["ui", "engine"]
    app: Optional[str] = None

class NodeList(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["node.list"] = "node.list"
    v: Literal[0] = 0
    nodes: list[NodeInfo]

class ParamSet(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["param.set"] = "param.set"
    v: Literal[0] = 0
    node: str
    path: str
    value: ParamValue

class FramePreview(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["frame.preview"] = "frame.preview"
    v: Literal[0] = 0
    node: str
    w: int
    h: int
    fps: float
    ms: float
    format: Literal["jpeg", "webp"]
    seq: int
    data: str

class GraphGet(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["graph.get"] = "graph.get"
    v: Literal[0] = 0

class GraphState(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["graph.state"] = "graph.state"
    v: Literal[0] = 0
    nodes: list[NodeInfo]
    edges: list[Edge]

class NodeAdd(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["node.add"] = "node.add"
    v: Literal[0] = 0
    node_type: str
    id: Optional[str] = None

class NodeRemove(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["node.remove"] = "node.remove"
    v: Literal[0] = 0
    node: str

class NodeConnect(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["node.connect"] = "node.connect"
    v: Literal[0] = 0
    src: str
    dst: str
    port: str

class NodeDisconnect(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["node.disconnect"] = "node.disconnect"
    v: Literal[0] = 0
    dst: str
    port: str

Message = Annotated[Union[Hello, NodeList, ParamSet, FramePreview, GraphGet, GraphState, NodeAdd, NodeRemove, NodeConnect, NodeDisconnect], Field(discriminator="type")]
_ADAPTER: TypeAdapter[Message] = TypeAdapter(Message)


def parse_message(data: object) -> Message:
    """dict/JSON → 판별 유니온으로 검증."""
    return _ADAPTER.validate_python(data)


def dump_message(msg: BaseModel) -> dict:
    return msg.model_dump()

// GENERATED — 편집 금지. 원천: packages/schema/protocol.schema.json
// 재생성: pnpm --filter @conode/schema generate
import { z } from 'zod';

export const PROTOCOL_VERSION = 0 as const;

export const ParamValue = z.union([z.number(), z.string(), z.boolean(), z.array(z.number())]);
export type ParamValue = z.infer<typeof ParamValue>;

export const Category = z.enum(["input", "vision", "depth", "generate", "audio", "output"]);
export type Category = z.infer<typeof Category>;

export const NodeInfo = z
	.object({
	"id": z.string(),
	"name": z.string(),
	"category": Category,
	"index": z.number().int(),
	"node_type": z.string().optional(),
	"inputs": z.array(z.string()).optional(),
	"params": z.record(z.unknown()).optional()
	})
	.strict();
export type NodeInfo = z.infer<typeof NodeInfo>;

export const Edge = z
	.object({
	"src": z.string(),
	"dst": z.string(),
	"port": z.string()
	})
	.strict();
export type Edge = z.infer<typeof Edge>;

export const Hello = z
	.object({
	"type": z.literal("hello"),
	"v": z.literal(0),
	"role": z.enum(["ui", "engine"]),
	"app": z.string().optional()
	})
	.strict();
export type Hello = z.infer<typeof Hello>;

export const NodeList = z
	.object({
	"type": z.literal("node.list"),
	"v": z.literal(0),
	"nodes": z.array(NodeInfo)
	})
	.strict();
export type NodeList = z.infer<typeof NodeList>;

export const ParamSet = z
	.object({
	"type": z.literal("param.set"),
	"v": z.literal(0),
	"node": z.string(),
	"path": z.string(),
	"value": ParamValue
	})
	.strict();
export type ParamSet = z.infer<typeof ParamSet>;

export const FramePreview = z
	.object({
	"type": z.literal("frame.preview"),
	"v": z.literal(0),
	"node": z.string(),
	"w": z.number().int(),
	"h": z.number().int(),
	"fps": z.number(),
	"ms": z.number(),
	"format": z.enum(["jpeg", "webp"]),
	"seq": z.number().int(),
	"data": z.string()
	})
	.strict();
export type FramePreview = z.infer<typeof FramePreview>;

export const GraphGet = z
	.object({
	"type": z.literal("graph.get"),
	"v": z.literal(0)
	})
	.strict();
export type GraphGet = z.infer<typeof GraphGet>;

export const GraphState = z
	.object({
	"type": z.literal("graph.state"),
	"v": z.literal(0),
	"nodes": z.array(NodeInfo),
	"edges": z.array(Edge)
	})
	.strict();
export type GraphState = z.infer<typeof GraphState>;

export const NodeAdd = z
	.object({
	"type": z.literal("node.add"),
	"v": z.literal(0),
	"node_type": z.string(),
	"id": z.string().optional()
	})
	.strict();
export type NodeAdd = z.infer<typeof NodeAdd>;

export const NodeRemove = z
	.object({
	"type": z.literal("node.remove"),
	"v": z.literal(0),
	"node": z.string()
	})
	.strict();
export type NodeRemove = z.infer<typeof NodeRemove>;

export const NodeConnect = z
	.object({
	"type": z.literal("node.connect"),
	"v": z.literal(0),
	"src": z.string(),
	"dst": z.string(),
	"port": z.string()
	})
	.strict();
export type NodeConnect = z.infer<typeof NodeConnect>;

export const NodeDisconnect = z
	.object({
	"type": z.literal("node.disconnect"),
	"v": z.literal(0),
	"dst": z.string(),
	"port": z.string()
	})
	.strict();
export type NodeDisconnect = z.infer<typeof NodeDisconnect>;

export const Message = z.discriminatedUnion('type', [Hello, NodeList, ParamSet, FramePreview, GraphGet, GraphState, NodeAdd, NodeRemove, NodeConnect, NodeDisconnect]);
export type Message = z.infer<typeof Message>;

export function parseMessage(u: unknown): Message {
	return Message.parse(u);
}
export function safeParseMessage(u: unknown) {
	return Message.safeParse(u);
}

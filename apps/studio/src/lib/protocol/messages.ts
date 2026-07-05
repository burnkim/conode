// GENERATED — 편집 금지. 원천: packages/schema/protocol.schema.json
// 재생성: pnpm --filter @conode/schema generate
import { z } from 'zod';

export const PROTOCOL_VERSION = 0 as const;

export const ParamValue = z.union([z.number(), z.string(), z.boolean()]);

export const Category = z.enum(["input", "vision", "depth", "generate", "audio", "output"]);

export const NodeInfo = z
	.object({
	"id": z.string(),
	"name": z.string(),
	"category": Category,
	"index": z.number().int()
	})
	.strict();

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

export const Message = z.discriminatedUnion('type', [Hello, NodeList, ParamSet, FramePreview]);
export type Message = z.infer<typeof Message>;

export function parseMessage(u: unknown): Message {
	return Message.parse(u);
}
export function safeParseMessage(u: unknown) {
	return Message.safeParse(u);
}

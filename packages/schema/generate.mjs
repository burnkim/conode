// conode 프로토콜 코드젠 — protocol.schema.json(원천) → zod(TS) + pydantic(Python).
// R3: UI↔엔진 계약은 이 스키마에서만 파생된다. 스키마 수정 후 재실행:
//   pnpm --filter @conode/schema generate
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, '..', '..');
const schema = JSON.parse(readFileSync(resolve(HERE, 'protocol.schema.json'), 'utf8'));
const defs = schema.$defs;
const PROTO_V = schema['x-protocol-version'] ?? 0;

const refName = (ref) => ref.split('/').pop();
const isMessage = (d) => d.type === 'object' && d.properties?.type?.const !== undefined;

// 생성 순서: 지원 타입 → 메시지 → 유니온
const ORDER = [
	'ParamValue',
	'Category',
	'NodeInfo',
	'Edge',
	'Hello',
	'NodeList',
	'ParamSet',
	'FramePreview',
	'GraphGet',
	'GraphState',
	'NodeAdd',
	'NodeRemove',
	'NodeConnect',
	'NodeDisconnect'
];
const MESSAGES = ORDER.filter((n) => isMessage(defs[n]));

const jsonLit = (v) => JSON.stringify(v);

// ---------- zod ----------
function zodField(s) {
	if (s.$ref) return refName(s.$ref);
	if (s.const !== undefined) return `z.literal(${jsonLit(s.const)})`;
	if (s.enum) return `z.enum([${s.enum.map(jsonLit).join(', ')}])`;
	if (s.oneOf) return `z.union([${s.oneOf.map(zodField).join(', ')}])`;
	switch (s.type) {
		case 'array':
			return `z.array(${zodField(s.items)})`;
		case 'integer':
			return `z.number().int()`;
		case 'number':
			return `z.number()`;
		case 'string':
			return `z.string()`;
		case 'boolean':
			return `z.boolean()`;
		default:
			throw new Error(`zod: 미지원 스키마 ${JSON.stringify(s)}`);
	}
}
function zodDef(name, d) {
	if (d.oneOf && !d.properties) return `export const ${name} = ${zodField(d)};`;
	if (d.enum && !d.properties) return `export const ${name} = ${zodField(d)};`;
	const req = new Set(d.required ?? []);
	const rows = Object.entries(d.properties).map(([k, v]) => {
		let expr = zodField(v);
		if (!req.has(k)) expr += '.optional()';
		return `\t${JSON.stringify(k)}: ${expr}`;
	});
	return `export const ${name} = z\n\t.object({\n${rows.join(',\n')}\n\t})\n\t.strict();`;
}
function emitZod() {
	const lines = [
		'// GENERATED — 편집 금지. 원천: packages/schema/protocol.schema.json',
		'// 재생성: pnpm --filter @conode/schema generate',
		"import { z } from 'zod';",
		'',
		`export const PROTOCOL_VERSION = ${PROTO_V} as const;`,
		''
	];
	for (const name of ORDER) {
		lines.push(zodDef(name, defs[name]));
		// 모든 스키마에 대응 타입 export (NodeInfo/Category/ParamValue 포함).
		lines.push(`export type ${name} = z.infer<typeof ${name}>;`);
		lines.push('');
	}
	lines.push(
		`export const Message = z.discriminatedUnion('type', [${MESSAGES.join(', ')}]);`,
		'export type Message = z.infer<typeof Message>;',
		'',
		'export function parseMessage(u: unknown): Message {',
		'\treturn Message.parse(u);',
		'}',
		'export function safeParseMessage(u: unknown) {',
		'\treturn Message.safeParse(u);',
		'}',
		''
	);
	return lines.join('\n');
}

// ---------- pydantic ----------
function pyField(s) {
	if (s.$ref) return refName(s.$ref);
	if (s.const !== undefined)
		return typeof s.const === 'string' ? `Literal[${jsonLit(s.const)}]` : `Literal[${s.const}]`;
	if (s.enum) return `Literal[${s.enum.map(jsonLit).join(', ')}]`;
	if (s.oneOf) {
		const parts = s.oneOf.map(pyField);
		// number|string|boolean → bool 우선(true/false 보존), int 포함
		if (parts.includes('float') && parts.includes('str'))
			return `Union[bool, int, float, str]`;
		return `Union[${parts.join(', ')}]`;
	}
	switch (s.type) {
		case 'array':
			return `list[${pyField(s.items)}]`;
		case 'integer':
			return 'int';
		case 'number':
			return 'float';
		case 'string':
			return 'str';
		case 'boolean':
			return 'bool';
		default:
			throw new Error(`py: 미지원 스키마 ${JSON.stringify(s)}`);
	}
}
function pyDef(name, d) {
	if (d.oneOf && !d.properties) return `${name} = ${pyField(d)}`;
	if (d.enum && !d.properties) return `${name} = ${pyField(d)}`;
	const req = new Set(d.required ?? []);
	const rows = Object.entries(d.properties).map(([k, v]) => {
		let ann = pyField(v);
		let line;
		if (v.const !== undefined) {
			line = `    ${k}: ${ann} = ${typeof v.const === 'string' ? jsonLit(v.const) : v.const}`;
		} else if (!req.has(k)) {
			line = `    ${k}: Optional[${ann}] = None`;
		} else {
			line = `    ${k}: ${ann}`;
		}
		return line;
	});
	return `class ${name}(BaseModel):\n    model_config = ConfigDict(extra="forbid")\n${rows.join('\n')}`;
}
function emitPy() {
	const lines = [
		'# GENERATED — 편집 금지. 원천: packages/schema/protocol.schema.json',
		'# 재생성: pnpm --filter @conode/schema generate',
		'from __future__ import annotations',
		'',
		'from typing import Annotated, Literal, Optional, Union',
		'',
		'from pydantic import BaseModel, ConfigDict, Field, TypeAdapter',
		'',
		`PROTOCOL_VERSION = ${PROTO_V}`,
		''
	];
	for (const name of ORDER) {
		lines.push(pyDef(name, defs[name]), '');
	}
	lines.push(
		`Message = Annotated[Union[${MESSAGES.join(', ')}], Field(discriminator="type")]`,
		'_ADAPTER: TypeAdapter[Message] = TypeAdapter(Message)',
		'',
		'',
		'def parse_message(data: object) -> Message:',
		'    """dict/JSON → 판별 유니온으로 검증."""',
		'    return _ADAPTER.validate_python(data)',
		'',
		'',
		'def dump_message(msg: BaseModel) -> dict:',
		'    return msg.model_dump()',
		''
	);
	return lines.join('\n');
}

// ---------- write ----------
const zodOut = resolve(ROOT, 'apps/studio/src/lib/protocol/messages.ts');
const pyOut = resolve(ROOT, 'engine/conode_engine/protocol/messages.py');
mkdirSync(dirname(zodOut), { recursive: true });
mkdirSync(dirname(pyOut), { recursive: true });
writeFileSync(zodOut, emitZod());
writeFileSync(pyOut, emitPy());
console.log(`generated:\n  ${zodOut}\n  ${pyOut}\n  messages: ${MESSAGES.join(', ')}`);

// 프로토콜 계약 테스트 (T4) — packages/schema/examples.json 공유 픽스처.
// engine/tests/test_protocol.py 와 동일 픽스처. 둘 다 통과해야 계약 성립 (R3).
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { Message, PROTOCOL_VERSION, type FramePreview } from './messages';

const here = dirname(fileURLToPath(import.meta.url));
const examples = JSON.parse(
	readFileSync(resolve(here, '../../../../../packages/schema/examples.json'), 'utf8')
) as { valid: unknown[]; invalid: unknown[] };

describe('protocol contract', () => {
	it('protocol version is 0', () => {
		expect(PROTOCOL_VERSION).toBe(0);
	});

	examples.valid.forEach((msg, i) => {
		const type = (msg as { type?: string }).type ?? '?';
		it(`accepts valid #${i} (${type})`, () => {
			const r = Message.safeParse(msg);
			expect(r.success ? null : JSON.stringify(r.error.issues)).toBe(null);
		});
	});

	examples.invalid.forEach((msg, i) => {
		const type = (msg as { type?: string }).type ?? '?';
		it(`rejects invalid #${i} (${type})`, () => {
			expect(Message.safeParse(msg).success).toBe(false);
		});
	});

	it('frame.preview roundtrips', () => {
		const fp: FramePreview = {
			type: 'frame.preview',
			v: 0,
			node: 'cam1',
			w: 320,
			h: 240,
			fps: 30,
			ms: 5,
			format: 'jpeg',
			seq: 1,
			data: 'AA'
		};
		expect(Message.safeParse(fp).success).toBe(true);
	});
});

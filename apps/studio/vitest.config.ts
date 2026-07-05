import { defineConfig } from 'vitest/config';

// 순수 TS(zod) 계약 테스트용 — SvelteKit 플러그인 불필요.
export default defineConfig({
	test: {
		environment: 'node',
		include: ['src/**/*.test.ts']
	}
});

import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

// @tauri-apps/cli sets this when running on a device / remote dev host.
const host = process.env.TAURI_DEV_HOST;

// https://vite.dev/config/  (Tauri conventions: fixed port, no clearScreen)
export default defineConfig({
	plugins: [sveltekit()],
	clearScreen: false,
	server: {
		port: 1420,
		strictPort: true,
		host: host || false,
		hmr: host
			? { protocol: 'ws', host, port: 1421 }
			: undefined,
		watch: {
			// Tauri sources are watched by cargo, not vite.
			ignored: ['**/src-tauri/**']
		}
	}
});

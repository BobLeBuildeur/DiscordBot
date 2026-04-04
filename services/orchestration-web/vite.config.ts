import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		proxy: {
			'/orchestrator': {
				target: 'http://localhost:8000',
				changeOrigin: true
			},
			'/auth': {
				target: 'http://localhost:8090',
				changeOrigin: true
			}
		}
	}
});

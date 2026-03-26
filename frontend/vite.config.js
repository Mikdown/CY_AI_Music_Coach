import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({
    plugins: [react()],
    server: {
        port: 5173,
        proxy: {
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
                logLevel: 'debug', // Enable debug logging
            }
        },
        // Increase timeout for long-running requests
        middlewareMode: false,
    }
});

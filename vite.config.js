// vite.config.js
import { resolve } from 'path'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
    plugins: [vue()],
    build: {
        manifest: true,
        rollupOptions: {
            input: {
                // editor: resolve(__dirname, './onto_spread_ed/templates/edit.html'),
                editor: resolve(__dirname, './js/editor/main.ts'),
                // admin: fileURLToPath(new URL('./resources/student/index.html', import.meta.url)),
                // release: fileURLToPath(new URL('./resources/auth/index.html', import.meta.url)),
            },
            output: {
                editor: resolve(__dirname, './onto_spread_ed/static/editor.js')
            }
        },
    },
})
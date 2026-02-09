import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import dts from 'vite-plugin-dts'

import { resolve } from 'path';

// https://vite.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [
    vue(),
    dts({
      include: ['src/**/*.ts', 'src/**/*.vue'],
      outDir: 'dist',
      tsconfigPath: './tsconfig.app.json',
    })
  ],
  build: {
    sourcemap: mode === 'production' ? true : 'inline',
    minify: mode === 'production',
    cssCodeSplit: true,
    esbuild: {
      drop: mode === 'production' || true ? ['console', 'debugger'] : [],
    },

    lib: {
      entry: resolve(__dirname, 'src/index.ts'),
      name: 'ose_js_core',
      fileName: 'index',
      formats: ['es'],
    },
    rollupOptions: {
      external: ['vue'],
      output: {
        globals: {
          vue: 'Vue'
        }
      }
    }
  }
}));

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

import { resolve } from 'path';

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  build: {
    outDir: resolve(__dirname, 'src/ose_plugin_bcio/static'),
    lib: {
      entry: resolve(__dirname, 'src/ose-plugin-bcio-js/index.ts'),
      name: 'ose_plugin_bcio',
      fileName: 'ose-plugin-bcio',
    },
    rollupOptions: {
      external: ['vue', '@ose/js-core'],
      output: {
        globals: {
          vue: 'Vue',
          '@ose/js-core': 'OseJsCore'
        }
      }
    }
  },
  resolve: {
  },
})

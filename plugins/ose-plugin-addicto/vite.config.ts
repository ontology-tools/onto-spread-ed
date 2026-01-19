import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

import { resolve } from 'path';

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  build: {
    outDir: resolve(__dirname, 'src/ose_plugin_addicto/static'),
    lib: {
      entry: resolve(__dirname, 'src/ose-plugin-addicto-js/index.ts'),
      name: 'ose_plugin_addicto',
      fileName: 'ose-plugin-addicto',
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

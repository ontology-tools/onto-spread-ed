import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import Components from 'unplugin-vue-components/vite';
import { BootstrapVueNextResolver } from 'bootstrap-vue-next';
import { resolve } from 'path';
import { readdirSync, existsSync } from 'fs';

// Dynamically discover entry points
const srcDir = resolve(__dirname, 'src');
const entries: Record<string, string> = {};

const dirs = readdirSync(srcDir);
for (const dir of dirs) {
  const entryPoint = resolve(srcDir, dir, 'main.ts');
  if (existsSync(entryPoint)) {
    entries[dir] = entryPoint;
  }
}

export default defineConfig(({mode}) => ({
  plugins: [
    vue(),
    Components({
      resolvers: [BootstrapVueNextResolver()],
    }),
  ],
  resolve: {
    alias: {
      '@ose/js-core': resolve(__dirname, '../ose-js-core/src'),
    },
  },
  build: {
    outDir: resolve(__dirname, '../../packages/ose-app/src/ose_app/static/js'),
    emptyOutDir: false,
    sourcemap: mode === 'production' ? false : 'inline',
    minify: mode === 'production',
    cssCodeSplit: true,
    esbuild: {
      drop: mode === 'production' ? ['console', 'debugger'] : [],
    },
    rollupOptions: {
      input: entries,
      output: {
        entryFileNames: '[name].js',
        chunkFileNames: 'chunks/[name]-[hash].js',
        assetFileNames: 'assets/[name][extname]',
      },
    },
  },
}));

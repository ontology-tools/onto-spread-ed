import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import Components from 'unplugin-vue-components/vite';
import { BootstrapVueNextResolver } from 'bootstrap-vue-next';
import { resolve } from 'path';
import type { Plugin } from 'vite';

// Dev server only: do what Flask's routes/spa.py does in production (prefix '').
// Keep in sync with spa.py. Vite itself moves the importmap before the first module script (postImportMapHook);
// OSE_CONFIG is a classic script, so it runs before the (deferred) modules.
const oseHead = (): Plugin => ({
  name: 'ose-head',
  apply: 'serve',
  transformIndexHtml: {
    handler(html) {
      const config = JSON.stringify({ prefix: '' });
      const importmap = JSON.stringify({
        imports: { 'vue': '/vue-shim.js', '@ontospreaded/js-core': '/ose-js-core-shim.js' },
      });
      return html.replace('<!--ose-head-->',
        `<script>window.OSE_CONFIG = ${config}</script>\n<script type="importmap">${importmap}</script>`);
    },
  },
});

const flask = `http://localhost:${process.env.FLASK_PORT ?? 5000}`;
const proxiedPaths = ['/api', '/login', '/logout', '/github-callback', '/status', '/static'];

export default defineConfig(({mode}) => ({
  base: './',
  plugins: [
    oseHead(),
    vue(),
    Components({
      resolvers: [BootstrapVueNextResolver()],
    }),
  ],
  resolve: {
    alias: {
      '@ontospreaded/js-core': resolve(__dirname, '../ose-js-core/src'),
    },
  },
  server: {
    port: 5173,
    strictPort: true,
    proxy: Object.fromEntries(proxiedPaths.map((p) => [p, { target: flask }])),
  },
  // Strip debug output in production, but keep console.error/warn for diagnosing problems
  esbuild: mode === 'production' ? {
    drop: ['debugger'],
    pure: ['console.log', 'console.debug'],
  } : {},
  build: {
    outDir: resolve(__dirname, '../ose-app/src/ose_app/static/app'),
    emptyOutDir: true,
    sourcemap: mode === 'production' ? false : 'inline',
    minify: mode === 'production',
  },
}));

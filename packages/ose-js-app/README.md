# OSE JS App

Vue 3 single-page app for OntoSpreadEd - the Ontology Spreadsheet Editor.

## Description

The whole web UI is this one SPA (vue-router, history mode). Flask (`ose-app`) only provides the JSON API
(`packages/ose-app/API.md`), the OAuth routes and static files, and serves the built app as a catch-all.
It includes:

- Spreadsheet editor with Tabulator.js integration
- Ontology visualization using D3.js and Graphviz
- Admin dashboard, index rebuild and settings pages
- Release management interface
- Common UI components

## Installation

This package is private and used as part of the main OntoSpreadEd application.

## Requirements

- Node.js 20.19+ (required by Vite 7)
- Vue 3

## Build

```bash
npm run build
```

Run it from the repository root: it builds `ose-js-core`, generates the plugin shims into `public/` and then builds this
package into `packages/ose-app/src/ose_app/static/app` (`npm -w @ontospreaded/js-app run build` alone needs the shims
and js-core build to exist already).

For development with `vite serve` (also from the root, generates the shims first):
```bash
npm run dev
```

Run Flask next to it (`make dev-python`, or `make dev` for both; the proxy targets `localhost:$FLASK_PORT`, default 5000) and open `http://localhost:5173`. A small plugin in
`vite.config.ts` injects `window.OSE_CONFIG` and the importmap (what Flask's `routes/spa.py` does in production), and the
dev server proxies `/api`, `/login`, `/logout`, `/github-callback`, `/status` and `/static` to Flask (`FLASK_PORT`, default 5000).
Use `localhost` (not `127.0.0.1`). The OAuth callback URL can keep pointing at Flask directly (`http://localhost:<FLASK_PORT>/github-callback`).
`npm -w @ontospreaded/js-app run watch` keeps the previous `vite build --watch` flow (open Flask directly).

## Structure

```
index.html        # Entry. CDN scripts (jQuery, bootbox, FontAwesome, Bootstrap bundle), <!--ose-head--> marker
public/           # Generated vue-shim.js / ose-js-core-shim.js (scripts/generate-shims.mjs)
src/
├── main.ts       # Sets window.Vue / window.OseJsCore for plugins, creates the app, installs bootstrap-vue-next + router
├── App.vue       # Shell: navbar, breadcrumb, branch picker, footer, <router-view>
├── router.ts     # Routes, history base = OSE_CONFIG.prefix
├── api.ts        # api() fetch helper, ApiError, useMe()
├── config.ts     # prefix, read from window.OSE_CONFIG
├── state.ts      # `layout` state for breadcrumb and branch picker
├── pages/        # Home, Repo (folder browser + search), LoggedOut, NotFound
├── editor/  visualise/  admin/  release/  settings/  common/
```

`index.html` contains the `<!--ose-head-->` marker. `ose_app/routes/spa.py` replaces it with `window.OSE_CONFIG = {prefix}` and the
importmap, and rewrites the relative asset URLs (`./assets/...`) to `{URL_PREFIX}/static/app/...`. There is no `<base>` tag.
Use `prefix` from `config.ts` for any URL that does not go through the router or `api()`.

## Routes

Defined in `src/router.ts`. Home and Repo are imported statically; the other pages (editor, visualise, admin, release) are lazy loaded.

| Path | Page |
|---|---|
| `/`, `/home` | `pages/Home.vue` (redirects to the repository if there is only one) |
| `/repo/:repo/:path(.*)*` | `pages/Repo.vue`, folder browser and search |
| `/edit/:repo/:path(.*)+` | `editor/Editor.vue` |
| `/visualise` | `visualise/Visualise.vue`, `meta.bare`: rendered without the shell, opened as a popup from the editor |
| `/admin/dashboard` (`/admin` redirects here) | `admin/Dashboard.vue` |
| `/admin/rebuild-index` | `admin/RebuildIndex.vue` |
| `/admin/release`, `/admin/release/:repo`, `/admin/release/:id(\d+)` | `release/Release.vue` |
| `/admin/settings` | `settings/Settings.vue` |
| `/admin/settings/:repo/:tab?` | `settings/ProjectSettings.vue` (tabs in `settings/project/`) |
| `/loggedout` | `pages/LoggedOut.vue` |
| `/direct?repo=&sheet=&go_to_row=&branch=` | Redirects to `/edit` (links of the former server-rendered app) |
| `/edit_external/:repo/:path(.*)*` | Redirects to `/repo` (former server-rendered page) |
| anything else | `pages/NotFound.vue` |

`?branch=` selects the branch on `/repo` and `/edit`; the editor also takes `?filter=` (JSON, e.g. `{"Label": "..."}`).

## API helper

`api<T>(path, init?)` in `src/api.ts` calls the backend and returns the parsed JSON.

- `path` is relative to the URL prefix (`/api/me`); the prefix is added automatically.
- Sends `Accept: application/json`, and `Content-Type: application/json` when the body is not `FormData`, `Blob` or `URLSearchParams`.
- On `401` it navigates to `{prefix}/login?next=<current url>` and never resolves.
- Any other non-2xx response throws `ApiError(status, message)`, where `message` is the response's `error`, else `message`, else `msg`, else the HTTP status text.
- `useMe()` returns `{me, ready}`: the cached `/api/me` response (user, permissions, app title/version/environment).
  `App.vue` uses it for the navbar, the admin link and the test-instance banner.

## Layout state

`layout` in `src/state.ts` (reactive) lets a page configure the shell of `App.vue`:

- `breadcrumb: {name, to?}[]`: crumbs after "Home"; a crumb without `to` is the current page.
- `branches`, `activeBranch`, `mainBranch`: when `activeBranch` is set, the branch picker is shown. Selecting a branch pushes `?branch=` to the
  current route, and breadcrumb links keep the active branch in their query.

The router resets the layout when the path changes, so each page sets it again once its data is loaded (see `pages/Repo.vue`).

## Adding a page

1. Create `src/<area>/MyPage.vue`. Load data with `api()` and set `layout.breadcrumb` (and branches if needed).
2. Add a lazy route in `src/router.ts` (`meta: {bare: true}` for no navbar/breadcrumb). Flask needs no change: its catch-all
   serves every non-`/api`, non-`/static` GET.
3. If the page needs data, add a JSON endpoint under `/api/` in `ose-app` (`routes/api/`, guarded by `requires_permissions`) and document it in `packages/ose-app/API.md`.
4. Link to it with `<RouterLink to="/...">`; never include the prefix, the router adds it.

## Plugins

Plugin components import `vue` and `@ontospreaded/js-core`, which the importmap resolves to the generated shims re-exporting
`window.Vue` / `window.OseJsCore` (set in `main.ts`). Modules are loaded with a dynamic import from
`{prefix}/api/plugins/<id>/static/<js_module>`.

## License

AGPL-3.0-or-later

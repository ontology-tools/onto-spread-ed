# OSE App API

JSON API served by Flask under `{URL_PREFIX}/api/*`. The Vue SPA (`packages/ose-js-app`) is its main client; see
`packages/ose-js-app/src/api.ts` for the fetch helper.

Blueprints: `src/ose_app/routes/api/*.py`. Permission names are those of `requires_permissions` /
`PermissionManager` (an `admin` user implicitly has all of them).

## Conventions

- Paths are relative to `URL_PREFIX`. Send and accept `application/json`.
- Requests under `/api/` never redirect or render HTML. Auth failures are always JSON, whatever the `Accept` header:
  - not logged in: `401 {"success": false, "error": string}`
  - missing permission: `403 {"success": false, "error": string}`
- This includes `/api` itself and unknown paths or wrong methods: any HTTP error (`404`, `405` with an `Allow` header,
  `400`, ...) and unhandled server errors (`500`, generic message) answer `{"success": false, "error": string}`.
- Errors generally look like `{"success": false, "error": string}`; some older endpoints use `{"msg": string}` or
  `{"error": string, "message": string}` instead.
- `/api/repo/{key}/tree`, `/api/repo/{key}/config` and the `/api/edit/*` endpoints answer `404` if the repository is not visible to the user. Other repository endpoints only check permissions.
- Login (`GET /login?next=<url>`, full page navigation), logout (`GET /logout`) and `GET /github-callback` are not part of the API.
  `GET /status/` returns `{"status": "ok"}`.

```ts
type Repo = { short: string; full: string }   // short key, GitHub owner/repo
```

## Current user

### GET /api/me  (public)

```ts
type Me = {
  logged_in: boolean
  app_title: string; app_version: string; environment: string | null; url_prefix: string
  // only when logged_in:
  login?: string                    // GitHub login
  initials?: string                 // initials of the user
  permissions?: string[]            // effective permissions after group/implication resolution
  all_initials?: (string | null)[]
}
```

## Repositories

### GET /api/repo/  (view)
`Repo[]`: the repositories visible to the user.

### GET /api/repo/{repo_key}/tree?branch={branch}  (view)
The whole tree of the branch (one GitHub git-trees call). Dot-entries and `scripts` directories are already filtered out.

```ts
type RepoTree = {
  repo_name: string; full_name: string       // full_name = GitHub owner/repo
  branches: string[]; active_branch: string; main_branch: string
  entries: { path: string; type: "dir" | "file" }[]   // flat, full paths from the root; files are *.xlsx
  truncated: boolean                         // GitHub cut the tree off (very large repositories); not paged
}
```

### GET /api/repo/{repo_key}/config  (view)
Configuration and branch info needed by the editor.

```ts
type RepoConfig = {
  repo_name: string
  repository_config: Record<string, any>    // Project, model_dump(mode="json")
  main_branch: string; branches: string[]
  initials: string; all_initials: (string | null)[]
}
```

### POST /api/repo/{repo}/install_workflow/{name}  (admin)
Installs the GitHub workflow template `{name}` into the repository. `{"success", "msg"}`.

## Editing

### GET /api/edit/get/{repo}/{path}?branch=  (view)
`{success, spreadsheet: {header, rows, file_sha, repo_name, folder, spreadsheet_name}}`.
GitHub communication errors answer `{success: false, error}` with status 200; other failures answer `500` JSON.

### GET /api/edit/suggestions/{repo}  (view)
`{success, suggestions: string[]}`: labels from the search index and the external ontology.

### POST /api/edit/save  (edit)
Body:

```ts
{ repo_key: string; path: string; rowData: string /* JSON string of rows */; initialData: string /* JSON string */;
  file_sha: string; commit_msg: string; commit_msg_extra: string; header: string[];
  merge_strategy?: "theirs" | "ours" | "automatic" | null; branch?: string | null }
```

Response: success `{success: true, new_rows, new_header, new_sha, merge_strategy}`; conflict
`{success: false, error: "merge-conflict", pr, file_sha_1, file_sha_2, merge_conflicts: [{row, col, base_value, our_value, their_value}], merged_table}`;
a missing or invalid request field (`repo_key`, `path`, `file_sha`, `header`, `rowData`, `initialData`, or
rowData/initialData that is not valid JSON) answers `400` with `{success: false, error}`; read-only file `405` and other failures `400` with `{success: false, error}`.

### POST /api/edit/check-updates  (view)
Body `{repo_key, folder, spreadsheet, file_sha, branch?}`, response `{up_to_date: boolean}`.

### PATCH /api/edit/{repo}/{path}  (edit)
Applies edits to a spreadsheet; the body is validated against `static/schema/req_body_edit.json`.

## Search

### GET /api/search/{repo}?query=&limit=  (view)
Term search over label and definition (`label` / `term` are accepted as aliases of `query`). Returns the raw searcher hits.

### POST /api/search/{repo}/sheets  (view)
Body `{query: string}` or `{initials: string}` (`initials` wins if both); `400` if neither is given.
Returns `SearchHit[]` with the fields `class_id, definition, label, parent, repo, spreadsheet`.

## Validation, external terms, visualisation

- `POST /api/validate/entity`, `POST /api/validate/file` (view): validation of a term resp. of a whole file.
- `POST /api/external/guess-parent` (view), `POST /api/external/{repo}/import` (edit): external term handling.
- `GET /api/visualise/dependencies/{repo}/{path}` (view): dependency and derived term data for the visualisation.

## Admin

### GET /api/admin/index  (index)
```ts
{ number_of_repositories: number; number_of_sheets: number; number_of_terms: number; repositories: string[]; sheets: string[] }
```

### POST /api/admin/index  (index)
Rebuilds the search index. No body. Returns `string[]` of the indexed sheets ("repo/file").

### GET /api/scripts/  (scripts)
`{success, result: {[id]: {title, arguments}}}`.

### POST /api/scripts/{name}/run  (scripts)
Body `{args: any[]}`, one value per script argument. `400` for unknown scripts or a wrong number of arguments.

## Settings

### GET /api/settings  (repository-config-view)
```ts
{ repositories: Record<string, any>[]      // loaded repositories, Project.model_dump(mode="json")
  startup_repositories: string[]; changing_startup_allowed: boolean; loading_new_allowed: boolean }
```

| Method and path | Permission |
|---|---|
| GET /api/settings/repositories/startup | repository-config-view |
| GET /api/settings/repositories/possibilities | repository-config-manage-loaded |
| POST /api/settings/repositories/load, /unload | repository-config-manage-loaded |
| POST /api/settings/repositories/add_startup, /remove_startup | repository-config-manage-startup |
| POST /api/settings/repositories/reload | admin |
| POST /api/settings/clear_caches | admin |

## Plugins

- `GET /api/plugins/`: info about all loaded plugins (no auth).
- `GET /api/plugins/{plugin_id}/static/{filename}`: files from the plugin's static folder, e.g. its `js_module` (no auth).

## Releases  (release)

| Method and path | Description |
|---|---|
| GET /api/release/ | All releases |
| GET /api/release/{id} | Release by numeric id |
| GET /api/release/{repo} | Releases of a repository |
| GET, POST /api/release/{repo}/running | The running release of a repository |
| POST /api/release/start | Start a release. Body `{repo, build_configuration}` (name or object) |
| GET /api/release/{repo}/continue?force= | Continue a paused release; `force` skips the failed stage |
| GET, POST /api/release/{repo}/rerun-step?force= | Re-run the current step |
| POST /api/release/{repo}/cancel | Cancel the running release |
| GET /api/release/download?release=&artifact= | Download a release artifact |
| GET, PUT /api/release/{repo}/release_script | Read / save the repository's project file |

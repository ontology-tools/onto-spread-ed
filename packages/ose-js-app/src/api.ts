import {ref} from "vue";

import {prefix} from "./config";

export {prefix};

export class ApiError extends Error {
    constructor(public status: number, message: string) {
        super(message);
    }
}

/** Fetch JSON from the backend. `path` is relative to the URL prefix, e.g. `/api/me`. */
export async function api<T = any>(path: string, init: RequestInit = {}): Promise<T> {
    const headers = new Headers(init.headers);
    headers.set("Accept", "application/json");
    const b = init.body;
    if (b && !headers.has("Content-Type") && !(b instanceof FormData || b instanceof Blob || b instanceof URLSearchParams)) {
        headers.set("Content-Type", "application/json");
    }

    const response = await fetch(prefix + path, {...init, headers});

    if (response.status === 401) {
        const next = encodeURIComponent(window.location.href);
        window.location.href = `${prefix}/login?next=${next}`;
        return new Promise<T>(() => {}); // never resolves, page is navigating away
    }

    let data: any = null;
    try {
        data = await response.json();
    } catch {
        // no JSON body
    }
    if (!response.ok) {
        throw new ApiError(response.status, data?.error ?? data?.message ?? data?.msg ?? response.statusText);
    }
    return data as T;
}

export type Me = {
    logged_in: boolean
    app_title: string
    app_version: string
    environment: string | null
    url_prefix: string
    login?: string
    initials?: string
    permissions?: string[]
    all_initials?: (string | null)[]
}

const me = ref<Me | null>(null);
let meRequest: Promise<void> | null = null;

/** Current user / app info from /api/me, fetched once and cached. */
export function useMe() {
    meRequest ??= api<Me>("/api/me").then(m => {
        me.value = m;
    }).catch(e => {
        meRequest = null;
        throw e;
    });
    return {me, ready: meRequest};
}

const cache = new Map<string, Promise<any>>();

function cached<T>(key: string, url: string): Promise<T> {
    let entry = cache.get(key);
    if (!entry) {
        entry = api<T>(url).catch(err => {
            if (cache.get(key) === entry) cache.delete(key);
            throw err;
        });
        cache.set(key, entry);
    }
    return entry;
}

/** Drop everything cached; call after changing repositories or their configuration. */
export const clearCache = () => cache.clear();

export type Repo = { short: string; full: string }
export type RepoTree = {
    repo_name: string; full_name: string
    branches: string[]; active_branch: string; main_branch: string
    entries: { path: string; type: "dir" | "file" }[]
    truncated: boolean
}

const treeKey = (repo: string, branch?: string) => `tree:${repo}:${branch ?? ""}`;

export const fetchRepos = () => cached<Repo[]>("repos", "/api/repo/");

export function fetchTree(repo: string, branch?: string) {
    return cached<RepoTree>(treeKey(repo, branch),
        `/api/repo/${repo}/tree` + (branch ? `?branch=${encodeURIComponent(branch)}` : ""));
}

export const fetchConfig = <T>(repo: string) => cached<T>(`config:${repo}`, `/api/repo/${repo}/config`);

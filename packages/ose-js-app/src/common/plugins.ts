/** One successfully loaded plugin entry point, identified by type and id. */
export interface PluginInfo {
    id: string;
    type: string;
    distribution: string | null;
    version: string | null;
    module_url?: string | null;
}

export function pluginTypeLabel(type: string): string {
    return ({
        "ose.build_stages": "Build stages",
        "ose.scripts": "Scripts",
        "ose.web_plugins": "Web plugin",
    } as Record<string, string>)[type] ?? type;
}

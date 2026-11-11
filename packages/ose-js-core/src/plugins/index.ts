import {defineAsyncComponent, type Component} from "vue";
import type {Release} from "../model";
import type {StageDetails} from "../release/stages";

export const PLUGIN_API_VERSION = 1 as const;

export interface StageViewProps<Data = StageDetails> {
    data?: Data | null;
    release: Release;
    selectedSubStep: string | null;
}

export type ReleaseControlEmit = {
    (event: "release-control", type: string, ...args: unknown[]): void;
};
export type StageViewLoader = () => Promise<Component | {default: Component}>;
export type StageView = Component | StageViewLoader;

export interface StageViewOptions {
    /**
     * The view lists the stage's warnings and infos itself. Otherwise, the host lists them below the view.
     */
    showsDiagnostics?: boolean;
}

export interface PluginContext {
    id: string;
    release: {
        addStageView(stageName: string, view: StageView, options?: StageViewOptions): void;
    };
}

export interface PluginDefinition {
    apiVersion: typeof PLUGIN_API_VERSION;
    setup(ose: PluginContext): void | Promise<void>;
}

export function definePlugin(plugin: PluginDefinition): PluginDefinition {
    return plugin;
}

const stageViews = new Map<string, {plugin: string; component: Component; options: StageViewOptions}>();

export const registry = {
    stageView(name: string): Component | undefined {
        return stageViews.get(name)?.component;
    },
    /** Options the view of a stage was registered with; empty for stages without a registered view */
    stageViewOptions(name: string): StageViewOptions {
        return stageViews.get(name)?.options ?? {};
    },
};

/** Registrations are committed only after setup succeeds. */
export async function setupPlugin(id: string, plugin: PluginDefinition): Promise<void> {
    if (plugin?.apiVersion !== PLUGIN_API_VERSION || typeof plugin.setup !== "function") {
        throw new Error(`Unsupported plugin API for ${id}`);
    }
    const pending = new Map<string, {component: Component; options: StageViewOptions}>();
    await plugin.setup({
        id,
        release: {
            addStageView(name, view, options = {}) {
                // Vue's function components must be passed through defineComponent;
                // a bare function here is a lazy loader.
                const component = typeof view === "function" ? defineAsyncComponent(view as StageViewLoader) : view;
                pending.set(name, {component, options: {...options}});
            },
        },
    });
    for (const [name, {component, options}] of pending) {
        const previous = stageViews.get(name);
        if (previous) {
            console.warn(`Stage view ${name} from ${previous.plugin} overridden by ${id}`);
        }
        stageViews.set(name, {plugin: id, component, options});
    }
}

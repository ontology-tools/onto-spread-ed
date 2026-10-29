import {definePlugin, setupPlugin} from "@ontospreaded/js-core";
import Validation from "./release/steps/Validation.vue";
import HumanVerification from "./release/steps/HumanVerification.vue";
import GithubPublish from "./release/steps/GithubPublish.vue";
import {api, prefix} from "./api";
import type {PluginInfo} from "./common/plugins";


export async function loadPlugins(): Promise<void> {
    await setupPlugin("builtin", definePlugin({
        apiVersion: 1,
        setup(ose) {
            ose.release.addStageView("VALIDATION", Validation);
            ose.release.addStageView("HUMAN_VERIFICATION", HumanVerification);
            ose.release.addStageView("GITHUB_PUBLISH", GithubPublish);
        },
    }));
    try {
        const plugins = await api<PluginInfo[]>("/api/plugins/");
        plugins.sort((a, b) => a.id < b.id ? -1 : a.id > b.id ? 1 : 0);
        for (const plugin of plugins) {
            if (!plugin.module_url) continue;
            try {
                const module = await import(/* @vite-ignore */ `${prefix}${plugin.module_url}`);
                await setupPlugin(plugin.id, module.default);
            } catch (error) {
                console.error(`Failed to load plugin ${plugin.id}:`, error);
            }
        }
    } catch (error) {
        console.error("Failed to discover plugins:", error);
    }
}

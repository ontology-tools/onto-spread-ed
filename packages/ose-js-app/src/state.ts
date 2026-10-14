import {reactive} from "vue";

export type Crumb = { name: string; to?: string };

/** Small shared state through which pages configure the breadcrumb and branch picker of App.vue. */
export const layout = reactive({
    breadcrumb: [] as Crumb[],
    branches: [] as string[],
    activeBranch: null as string | null,
    mainBranch: null as string | null,
});

export function resetLayout() {
    layout.breadcrumb = [];
    layout.branches = [];
    layout.activeBranch = null;
    layout.mainBranch = null;
}

import {createRouter, createWebHistory} from "vue-router";
import {prefix} from "./config";
import {resetLayout} from "./state";
import Home from "./pages/Home.vue";
import Repo from "./pages/Repo.vue";

export const router = createRouter({
    history: createWebHistory(prefix || "/"),
    routes: [
        {path: "/", component: Home},
        {path: "/home", component: Home},
        {path: "/repo/:repo/:path(.*)*", name: "repo", component: Repo},
        {path: "/edit/:repo/:path(.*)+", name: "edit", component: () => import("./editor/Editor.vue")},
        // Links of the former server-rendered pages
        {
            path: "/direct",
            redirect: to => {
                const {repo, sheet, go_to_row, branch} = to.query;
                if (typeof repo !== "string" || typeof sheet !== "string") return "/";
                const query: Record<string, string> = {};
                if (typeof go_to_row === "string") query.filter = JSON.stringify({Label: go_to_row});
                if (typeof branch === "string") query.branch = branch;
                return {name: "edit", params: {repo, path: sheet.split("/")}, query};
            },
        },
        {path: "/edit_external/:repo/:path(.*)*", redirect: to => ({name: "repo", params: to.params})},
        {path: "/visualise", component: () => import("./visualise/Visualise.vue"), meta: {bare: true}},
        {path: "/admin", component: () => import("./admin/Dashboard.vue")},
        {path: "/admin/dashboard", component: () => import("./admin/Dashboard.vue")},
        {path: "/admin/rebuild-index", component: () => import("./admin/RebuildIndex.vue")},
        {path: "/admin/release", component: () => import("./release/Release.vue")},
        {path: "/admin/release/:repo", component: () => import("./release/Release.vue")},
        {path: "/admin/release/:id(\\d+)", component: () => import("./release/Release.vue")},
        {path: "/admin/settings", component: () => import("./settings/Settings.vue")},
        {path: "/forbidden", component: () => import("./pages/Forbidden.vue")},
        {path: "/loggedout", component: () => import("./pages/LoggedOut.vue")},
        {path: "/:pathMatch(.*)*", component: () => import("./pages/NotFound.vue")},
    ],
});

// Pages that fill the breadcrumb/branch picker overwrite it themselves right away; for all others, clear it.
router.afterEach((to, from, failure) => {
    if (!failure && to.path !== from.path && to.name !== "repo" && to.name !== "edit") resetLayout();
});

import {definePlugin} from "@ontospreaded/js-core";

export default definePlugin({
    apiVersion: 1,
    setup(ose) {
        ose.release.addStageView("BCIO_SEARCH", () => import("./BCIOSearch.vue"));
    },
});

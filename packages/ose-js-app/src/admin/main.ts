import {createApp} from "vue";
import Dashboard from "./Dashboard.vue";
import {$filters} from "@ontospreaded/js-core";


const app = createApp(Dashboard)

app.config.globalProperties.$filters = $filters

app.mount("#vue-app-dashboard")

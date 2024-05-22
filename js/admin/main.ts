import {createApp} from "vue";
import Dashboard from "./Dashboard.vue";
import {$filters} from "../common/filter";


const app = createApp(Dashboard)

app.config.globalProperties.$filters = $filters

app.mount("#vue-app-dashboard")

import {createApp} from "vue";
import Settings from "./Settings.vue";
import {$filters} from "../common/filter";


const app = createApp(Settings)

app.config.globalProperties.$filters = $filters

app.mount("#vue-app-settings")

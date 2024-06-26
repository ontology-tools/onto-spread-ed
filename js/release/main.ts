import {createApp} from "vue";
import Release from "./Release.vue";
import {$filters} from "../common/filter";


const app = createApp(Release)


app.config.globalProperties.$filters = $filters

app.mount("#vue-app-release")

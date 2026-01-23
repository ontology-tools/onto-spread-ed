import {createApp} from "vue";
import Release from "./Release.vue";
import {$filters} from "@ose/js-core";


const app = createApp(Release)


app.config.globalProperties.$filters = $filters

app.mount("#vue-app-release")

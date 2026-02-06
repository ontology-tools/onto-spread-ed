import {createApp} from "vue";
import Release from "./Release.vue";
import {$filters} from "@ose/js-core";
import { createBootstrap } from "bootstrap-vue-next";


const app = createApp(Release)


app.use(createBootstrap())

app.config.globalProperties.$filters = $filters

app.mount("#vue-app-release")

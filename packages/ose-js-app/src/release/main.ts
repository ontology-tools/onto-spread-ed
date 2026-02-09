import * as Vue from "vue";
import * as OseJsCore from "@ose/js-core";
import {createApp} from "vue";
import Release from "./Release.vue";
import {$filters} from "@ose/js-core";
import { createBootstrap } from "bootstrap-vue-next";

// Expose Vue and @ose/js-core globally for dynamically loaded plugin components
(window as any).Vue = Vue;
(window as any).OseJsCore = OseJsCore;

const app = createApp(Release)


app.use(createBootstrap())

app.config.globalProperties.$filters = $filters

app.mount("#vue-app-release")

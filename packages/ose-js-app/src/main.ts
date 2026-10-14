import * as Vue from "vue";
import {createApp} from "vue";
import * as OseJsCore from "@ontospreaded/js-core";
import {$filters} from "@ontospreaded/js-core";
import {createBootstrap} from "bootstrap-vue-next";

import "bootstrap-vue-next/dist/bootstrap-vue-next.css";
// Includes bootstrap itself with the app's theme
import "./main.scss";

import App from "./App.vue";
import {router} from "./router";

// Expose Vue and @ontospreaded/js-core globally for dynamically loaded plugin components
(window as any).Vue = Vue;
(window as any).OseJsCore = OseJsCore;

declare module "vue" {
  interface ComponentCustomProperties {
    $filters: typeof $filters
  }
}

const app = createApp(App);

app.use(createBootstrap());
app.use(router);

app.config.globalProperties.$filters = $filters;

app.mount("#app");

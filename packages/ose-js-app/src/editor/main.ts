// // add the beginning of your app entry
// import 'vite/modulepreload-polyfill'

import {createApp} from "vue";
import Editor from "./Editor.vue";
import {createBootstrap} from 'bootstrap-vue-next'

// Add the necessary CSS
import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue-next/dist/bootstrap-vue-next.css'

import {$filters} from "@ose/js-core";

const app = createApp(Editor)


app.use(createBootstrap())

app.config.globalProperties.$filters = $filters

app.mount("#vue-app-editor")

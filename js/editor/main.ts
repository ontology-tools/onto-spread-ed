import {createApp} from "vue";
import Editor from "./Editor.vue";
import {$filters} from "../common/filter";


const app = createApp(Editor)
// import {createBootstrap} from 'bootstrap-vue-next'

app.config.globalProperties.$filters = $filters

// app.use(createBootstrap())
app.mount("#vue-app-editor")

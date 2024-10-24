import {createApp} from "vue";
import Settings from "./Settings.vue";
import {$filters} from "../common/filter";


const app = createApp(Settings)
// import {createBootstrap} from 'bootstrap-vue-next'

app.config.globalProperties.$filters = $filters

// app.use(createBootstrap())
app.mount("#vue-app-settings")

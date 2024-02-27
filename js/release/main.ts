import {createApp} from "vue";
import Release from "./Release.vue";
import Preparation from "./Setup.vue";


const app = createApp(Release)

app.component("Preparation", Preparation)

app.mount("#vue-app-release")

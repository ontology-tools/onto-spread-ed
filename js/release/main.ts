import {createApp} from "vue";
import Release from "./Release.vue";


const app = createApp(Release)

app.config.globalProperties.$filters = {
    formatDate(d: string | Date): string {
        const date = d instanceof Date ? d : new Date(d)
        return new Intl.DateTimeFormat("default", {dateStyle: "long", timeStyle: "short"}).format(date)
    },
    formatText(str: string): string {
        const s = str.trim().toLowerCase().replace("_", " ")
        return s.charAt(0).toUpperCase() + s.substring(1)
    }
}

app.mount("#vue-app-release")

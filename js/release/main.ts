import {createApp} from "vue";
import Release from "./Release.vue";


const app = createApp(Release)

function pluralise(str: string): string;
function pluralise(str: string, list: any[]): string;
function pluralise(str: string, amount: number): string;
function pluralise(str: string, listOrAmount?: any[] | number): string {
    let amount: number;
    if (Array.isArray(listOrAmount)) {
        amount = listOrAmount.length;
    } else if (listOrAmount) {
        amount = listOrAmount;
    } else {
        amount = 2;
    }

    if (amount < 2) {
        return str;
    }

    if (str?.endsWith("y")) {
        return str.substring(0, str.length - 1) + "ies";
    }

    if (str) {
        return str + "s";
    }

    return str;
}

app.config.globalProperties.$filters = {
    formatDate(d: string | Date): string {
        const date = d instanceof Date ? d : new Date(d)
        return new Intl.DateTimeFormat("default", {dateStyle: "long", timeStyle: "short"}).format(date)
    },
    formatText(str: string): string {
        const s = str.trim().toLowerCase().replace("_", " ")
        return s.charAt(0).toUpperCase() + s.substring(1)
    },
    pluralise

}

app.mount("#vue-app-release")

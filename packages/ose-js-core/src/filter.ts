export function pluralise(str: string): string;
export function pluralise(str: string, list: any[]): string;
export function pluralise(str: string, amount: number): string;
export function pluralise(str: string, listOrAmount?: any[] | number): string {
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

export function formatText(str: string): string {
    const s = str.trim().toLowerCase().replace("_", " ")
    return s.charAt(0).toUpperCase() + s.substring(1)
}

export function formatDate(d: string | Date): string {
    const date = d instanceof Date ? d : new Date(d)
    return new Intl.DateTimeFormat("default", {dateStyle: "long", timeStyle: "short"}).format(date)
}

export const $filters = {
    formatDate,
    formatText,
    pluralise
}
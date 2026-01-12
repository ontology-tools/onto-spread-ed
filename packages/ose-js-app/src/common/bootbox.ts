export type PromptOptions = Omit<BootboxPromptOptions, "callback">

export function promptDialog<T = string>(options: PromptOptions): Promise<T | null> {
    return new Promise(resolve => {
        bootbox.prompt({
            ...options,
            callback(result: string | null) {
                resolve(result as T ?? null)
            }
        })
    })
}

export type AlertOptions = Omit<BootboxAlertOptions, "callback">

export function alertDialog<T = string>(options: AlertOptions, resumeAfter: "callback" | "hidden" = "hide"): Promise<T | null> {
    return new Promise(resolve => {
        let value: T | null = null;
        bootbox.alert({
            ...options,
            onHidden() {
                if (resumeAfter === "hidden") {
                    resolve(value)
                }
            },
            callback(result: T | null) {
                if (resumeAfter === "hidden") {
                    value = result ?? null;
                } else {
                    resolve(result ?? null)
                }
            }
        })

    })
}

export type ConfirmOptions = Omit<BootboxConfirmOptions, "callback">

export function confirmDialog(options: ConfirmOptions): Promise<boolean> {
    return new Promise(resolve => {
        bootbox.confirm({
            ...options,
            callback(result: boolean) {
                resolve(result)
            }
        })
    })
}

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

export function alertDialog<T = string>(options: AlertOptions): Promise<T | null> {
    return new Promise(resolve => {
        bootbox.alert({
            ...options,
            callback(result: T | null) {
                resolve(result ?? null)
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

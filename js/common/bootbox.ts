export type PromptOptions = Omit<BootboxPromptOptions, "callback">

export function promptDialog(options: PromptOptions): Promise<string | null> {
    return new Promise(resolve => {
        bootbox.prompt({
            ...options,
            callback(result: string | null) {
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

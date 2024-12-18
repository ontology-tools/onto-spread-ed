export function debounce<U extends unknown[], R>(func: (...args: U) => (R | Promise<R>), timeout: number = 100): (...args: U) => Promise<R> {
    let timer: number;
    return (...args: U) => {
        clearTimeout(timer);
        return new Promise(resolve => {
            timer = setTimeout(() => {
                const r = func.apply(undefined, args);
                if (r instanceof Promise) {
                    r.then(resolve);
                } else {
                    resolve(r);
                }
            }, timeout);
        })
    };
}

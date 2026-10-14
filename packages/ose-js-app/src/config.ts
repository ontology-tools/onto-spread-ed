declare global {
    interface Window {
        OSE_CONFIG?: { prefix: string };
    }
}

/** Runtime URL prefix of the deployment, injected by Flask into index.html. */
export const prefix: string = window.OSE_CONFIG?.prefix ?? "";

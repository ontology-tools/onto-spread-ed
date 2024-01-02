declare var release: Release | null;

if (release) {
    release.start = new Date(release.start)
    release.end = new Date(release.end)
}

interface Release<D = Date> {
    id: number
    state: string
    running: boolean
    step: number
    details: object
    started_by: string,
    start: D
    end: D
    worker_id: string,
    included_files: string[]
}

function activate_tooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))
}

document.body.onload = async () => {
    const core: HTMLDivElement = document.querySelector("#release-core")!
    const icon_release: HTMLElement = document.querySelector("#icon-release")!
    const release_info: HTMLSpanElement = document.querySelector("#release-info")!
    const btn_start_release: HTMLLinkElement | null = document.querySelector("#btn-start-release")
    const btn_release_restart: HTMLLinkElement | null = document.querySelector("#btn-release-restart")
    const btn_release_rerun_step: HTMLButtonElement | null = document.querySelector("#btn-release-rerun-step")
    const btn_release_cancel: HTMLButtonElement | null = document.querySelector("#btn-release-cancel")
    const btn_refresh: HTMLButtonElement | null = document.querySelector("#btn-release-refresh")
    const tgl_auto_refresh: HTMLInputElement | null = document.querySelector("#tgl-auto-refresh")
    const control_buttons = [
        btn_start_release,
        btn_release_restart,
        btn_release_rerun_step,
        btn_release_cancel,
        btn_refresh,
        tgl_auto_refresh
    ]

    let selected_step: number | null = null;

    const steps_without_auto_refresh = [NaN, -1, 6]

    let btn_publish_release: HTMLButtonElement | null;

    let refresh_interval: number | undefined = undefined;

    async function set_disabled_all(disabled: boolean = true) {
        btn_start_release?.setAttribute("disabled", String(disabled))
        if (disabled) {
            control_buttons.forEach(b => b?.setAttribute("disabled", "true"))
        } else {
            control_buttons.forEach(b => b?.removeAttribute("disabled"))
        }
    }

    // let release: Release | null = null

    async function update() {
        activate_tooltips();
        await set_disabled_all(false)

        const urlParams = new URLSearchParams(window.location.search);
        const step_str = urlParams.get("step")
        selected_step = Number.parseInt(step_str ?? "NaN")
        if (Number.isNaN(selected_step)) {
            selected_step = release?.step ?? null
        }

        if (release?.worker_id === null && release.state !== "canceled" && release.state !== "completed") {
            btn_release_rerun_step?.classList.remove("d-none")
        } else {
            btn_release_rerun_step?.classList.add("d-none")
        }

        if (release === null || release.state === "canceled" || release.state === "completed") {
            btn_release_cancel?.classList.add("d-none")
            btn_release_restart?.classList.add("d-none")
        } else {
            btn_release_cancel?.classList.remove("d-none")
            btn_release_restart?.classList.remove("d-none")
        }

        icon_release.classList.remove(...icon_release.classList)
        switch (release?.state) {
            case undefined:
            case null:
                icon_release.classList.add("fa-regular", "fa-file", "text-black-50")
                break;
            case "canceled":
                icon_release.classList.add("fa-regular", "fa-circle-xmark", "text-danger")
                break;
            case "waiting-for-user":
                icon_release.classList.add("fa-solid", "fa-user-clock", "text-warning")
                break;
            case "errored":
                icon_release.classList.add("fa-solid", "fa-triangle-exclamation", "text-danger")
                break;
            case "completed":
                icon_release.classList.add("fa-regular", "fa-circle-check", "text-success")
                break;
            default:
                icon_release.classList.add("fa", "fa-spinner", "fa-spin", "text-black-50")
                break;
        }
        icon_release.title = release?.state ?? "not started"
        release_info.innerText = release ? `started by ${release.started_by} at ${release.start.toLocaleString()}` : ""

        const validation_sidebar_links: NodeListOf<HTMLButtonElement> = document.querySelectorAll(".btn-validation")
        const validation_elements = document.querySelectorAll(".val")
        for (const btn of validation_sidebar_links) {
            btn.addEventListener("click", (event) => {
                const file = btn.getAttribute("data-ose-file")
                console.log(file)
                for (const element of validation_elements) {
                    element.classList.add("d-none")
                }

                for (const element of document.querySelectorAll(`.val-error-source-${file}, .val-warning-source-${file}`)){
                    element.classList.remove("d-none")
                }

                for (const btn of validation_sidebar_links) {
                    btn.classList.remove("fw-bold")
                }
                btn.classList.add("fw-bold")
                clearInterval(refresh_interval)
            })
        }


        const publish_checklist: HTMLInputElement[] = Array.from(document.querySelectorAll(".checklist"))
        btn_publish_release = document.querySelector("#btn-publish-release")
        if (btn_publish_release !== null) {
            btn_publish_release.addEventListener("click", async (event) => {
                if (btn_publish_release?.disabled === false) {
                    await set_disabled_all()
                    btn_publish_release.setAttribute("disabled", "true")
                    for (const check of publish_checklist) {
                        check.setAttribute("disabled", "true")
                    }

                    await fetch("/api/release/continue")
                    await refresh()

                    tgl_auto_refresh?.click()
                }
            })
        }

        function update_btn_publish_disabled() {
            if (publish_checklist.every(x => x.checked)) {
                btn_publish_release?.removeAttribute("disabled")
            } else {
                btn_publish_release?.setAttribute("disabled", "true")
            }
        }

        for (const check of publish_checklist) {
            check.addEventListener("change", event => {
                update_btn_publish_disabled()
            })
        }

        update_btn_publish_disabled()

        if (steps_without_auto_refresh.includes(selected_step ?? NaN) || release?.running == false) {
            clearInterval(refresh_interval)
            if (tgl_auto_refresh !== null) {
                tgl_auto_refresh.checked = false
                tgl_auto_refresh.setAttribute("disabled", "true")
            }
        }
    }

    await update()

    async function refresh() {
        const id = window.location.href.match(/release(\/\d+)/)?.[1] ?? ""
        const suffix = selected_step === (release?.step ?? null) ? "" : `?step=${selected_step}`
        const response = await fetch(`/admin/release/core${id}${suffix}`)
        const data = await response.json()

        release = data["release"]
        if (release) {
            release.start = new Date(release.start)
            release.end = new Date(release.end)
        }
        core.innerHTML = data["html"]

        await update()
    }

    if (tgl_auto_refresh !== null) {
        tgl_auto_refresh.addEventListener("change", (event) => {
            clearInterval(refresh_interval)
            if (tgl_auto_refresh.checked) {
                refresh_interval = setInterval(refresh, 2000)
                console.debug("Starting refresh interval")
            }
        })
    }

    if (btn_refresh !== null) {
        btn_refresh.addEventListener("click", async (event) => {
            await set_disabled_all()
            await refresh()
        })
    }

    if (btn_release_rerun_step !== null) {
        btn_release_rerun_step.addEventListener("click", async event => {
            event.preventDefault()
            await set_disabled_all()

            await fetch("/api/release/rerun-step", {
                method: "POST"
            })

            await refresh()
        })
    }

    if (btn_release_cancel !== null) {
        btn_release_cancel.addEventListener("click", async event => {
            event.preventDefault()
            await set_disabled_all()

            await fetch("/api/release/cancel", {
                method: "POST"
            })
        })
    }


    if (btn_start_release !== null) {
        btn_start_release.addEventListener("click", async (event) => {
            event.preventDefault()
            await set_disabled_all()

            const files = Array.from(document.querySelectorAll("[data-ose-file-name]"))
                .filter(e => e instanceof HTMLInputElement && e.checked)
                .map(e => e.getAttribute("data-ose-file-name"))

            const response = await fetch("/api/release/BCIO/start", {
                method: "POST",
                body: JSON.stringify({
                    files
                }),
                headers: {
                    "Content-type": "application/json; charset=UTF-8"
                }
            })
            const started_release: Release = await response.json()
            window.location.href += "/" + started_release.id
        })
    } else {
        if (tgl_auto_refresh?.checked) {
            clearInterval(refresh_interval)
            refresh_interval = setInterval(refresh, 2000)
            console.debug("Starting refresh interval")
        }
    }

    if (btn_release_restart !== null) {
        btn_release_restart.addEventListener("click", async (event) => {
            event.preventDefault()
            await set_disabled_all()

            clearInterval(refresh_interval)
            const files = release?.included_files

            await fetch("/api/release/cancel", {
                method: "POST"
            })

            if (files === undefined) {
                window.location.reload()
            } else {
                const response = await fetch("/api/release/BCIO/start", {
                    method: "POST",
                    body: JSON.stringify({
                        files
                    }),
                    headers: {
                        "Content-type": "application/json; charset=UTF-8"
                    }
                })
                const started_release: Release = await response.json()
                window.location.href += "/" + started_release.id
                }

        })
    }

}


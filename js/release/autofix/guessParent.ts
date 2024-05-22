import {AutoFixState, Diagnostic, Term, TermIdentifier} from "../model.ts";
import {confirmDialog, promptDialog} from "../../common/bootbox.ts";

export interface ParentGuess {
    ontology_id: string,
    term: TermIdentifier,
    kind: "internal" | "external"
}

declare var URLS: { [key: string]: any }
const prefix_url = URLS.prefix

async function guessInternal(_: Term, repo: string, defined_parent?: TermIdentifier): Promise<ParentGuess[] | null> {
    if (!defined_parent || !defined_parent.label) {
        return null
    }

    try {
        const response = await fetch(`${prefix_url}/api/search/${repo}?` + new URLSearchParams({
            label: defined_parent.label
        }))

        const data: any[] = await response.json()
        return data.flatMap((x: any) => x["label"] && x["class_id"] ? [{
            term: {
                label: x["label"],
                id: x["class_id"]
            },
            ontology_id: repo,
            kind: "internal"
        }] : [])
    }catch {}

    return null
}

export async function guessExternal(term: Term, _: string, defined_parent?: TermIdentifier): Promise<ParentGuess[] | null> {
    try {
        const response = await fetch(`${prefix_url}/api/external/guess-parent`, {
            method: "post",
            body: JSON.stringify({
                term: {
                    id: term.id ?? undefined,
                    label: term.label ?? undefined
                },
                parent: {
                    id: defined_parent?.id ?? undefined,
                    label: defined_parent?.label ?? undefined
                },
            }),
            headers: {
                "Content-Type": "application/json"
            }
        })

        const parent: ParentGuess[] = await response.json()
        if (parent) {
            return parent.map(x => ({...x, kind: "external"}))
        }
    } catch {
    }

    return null
}


async function singleExternalGuess(error: Diagnostic, repo: string, guess: ParentGuess): Promise<AutoFixState> {
    const parent = guess.term
    const result = await confirmDialog({
        title: "Found an external parent",
        message:
            `An external parent <code>${parent.label}</code> (<code>${parent.id}</code>) of ` +
            `<code>${error.term.label}</code> (<code>${error.term.id}</code>) was found. Import the term?`,
        buttons: {
            confirm: {
                label: `Import ${parent.id}`,
                className: "btn-success",
            },
            cancel: {
                label: "Cancel",
                className: "btn-warning"
            }
        }
    })

    if (result) {
        try {
            const response = await fetch(`${prefix_url}/api/external/${repo}/import`, {
                method: "post",
                body: JSON.stringify({
                    terms: [{id: parent.id, label: parent.label}],
                    ontologyId: guess.ontology_id
                }),
                headers: {"Content-Type": "application/json"}
            })

            if (response.ok) {
                return "fixed"
            }
        } catch {
            return "impossible"
        }
    }

    return "loaded"
}

async function multipleExternalGuesses(guesses: ParentGuess[], error: Diagnostic, repo: string): Promise<AutoFixState> {
    const index = await promptDialog({
        title: "Found possible external parents",
        message:
            `Found ${guesses.length} possible external terms for <code>${error.parent.label}</code>. ` +
            `Select the correct parent term of <code>${error.term.label}</code> (<code>${error.term.id}</code>) ` +
            `if it is in the list.`,
        inputType: "select",
        inputOptions: guesses.map((g, i) => ({value: i.toString(), text: `${g.term.label} (${g.term.id})`})),
        buttons: {
            confirm: {
                label: `Import the selected term`,
                className: "btn-success",
            },
            cancel: {
                label: "Cancel",
                className: "btn-warning"
            }
        }
    })

    if (index !== null) {
        const guess = guesses[+index]
        const parent = guess.term;
        try {
            const response = await fetch(`${prefix_url}/api/external/${repo}/import`, {
                method: "post",
                body: JSON.stringify({
                    terms: [{
                        id: parent.id,
                        label: parent.label
                    }],
                    ontologyId: guess.ontology_id
                }),
                headers: {"Content-Type": "application/json"}
            })

            if (response.ok) {
                return "fixed"
            } else {
                return "impossible"
            }
        } catch {
            return "impossible"
        }
    }

    return "loaded"
}


async function multipleInternalGuesses(guesses: ParentGuess[], error: Diagnostic, repo: string): Promise<AutoFixState> {
    const index = await promptDialog({
        title: `Found possible parent in ${repo}`,
        message:
            `Found ${guesses.length} possible terms for <code>${error.parent.label}</code> in ${repo}. ` +
            `Select the correct parent term of <code>${error.term.label}</code> (<code>${error.term.id}</code>) ` +
            `if it is in the list or search for external terms.`,
        inputType: "select",
        inputOptions: guesses.map((g, i) => ({value: i.toString(), text: `${g.term.label} (${g.term.id})`})),
        buttons: {
            confirm: {
                label: `Set as parent`,
                className: "btn-success",
            },
            cancel: {
                label: "Search for external term",
                className: "btn-primary"
            }
        }
    })

    if (index !== null) {
        const guess = guesses[+index]
        const parent = guess.term;
        try {
            const response = await fetch(`${prefix_url}/api/edit/${repo}/${error.term.origin[0]}`, {
                method: "PATCH",
                body: JSON.stringify({
                    term: {
                        id: error.term.id,
                        parent: parent.label
                    }
                }),
                headers: {"Content-Type": "application/json"}
            })

            if (response.ok) {
                return "fixed"
            } else {
                return "impossible"
            }
        } catch {
            return "impossible"
        }
    }

    return "loaded"
}

export async function guessParent(error: Diagnostic, repo: string): Promise<AutoFixState> {
    let guesses = await guessInternal(error.term, repo, error.parent)
    if (guesses !== null && guesses.length > 0) {
        const response = await multipleInternalGuesses(guesses, error, repo)
        if (response !== "loaded") {
            return response
        }
    }

    guesses = await guessExternal(error.term, repo, error.parent)
    if (guesses !== null && guesses.length > 0) {
        if (guesses.length === 1) {
            return await singleExternalGuess(error, repo, guesses[0])
        } else {
            return await multipleExternalGuesses(guesses, error, repo);
        }
    }

    return "impossible"
}

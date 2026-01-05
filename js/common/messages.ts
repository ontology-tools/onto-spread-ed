export interface NavigateToSheetMessage {
    type: "navigateToSheet";
    repo: string;
    sheet: string;
    filter: { [key: string]: string };
}

export function isNavigateToSheetMessage(msg: any): msg is NavigateToSheetMessage {
    return (
        msg &&
        msg.type === "navigateToSheet" &&
        typeof msg.repo === "string" &&
        typeof msg.sheet === "string" &&
        typeof msg.filter === "object"
    );
}

export interface NavigateToTermMessage {
    type: "navigateToTerm";
    repo: string;
    sheet: string;
    termID?: string;
    termLabel?: string;
};

export function isNavigateToTermMessage(msg: any): msg is NavigateToTermMessage {
    return (
        msg &&
        msg.type === "navigateToTerm" &&
        typeof msg.repo === "string" &&
        typeof msg.sheet === "string" &&
        (typeof msg.termId === "string" || typeof msg.termLabel === "string")
    );
}

export interface FocusWindowMessage {
    type: "focusEditor";
}

export function isFocusWindowMessage(msg: any): msg is FocusWindowMessage {
    return msg && msg.type === "focusEditor";
}

export interface ScrollToRowMessage {
    type: "scrollToRow";
    position: number;
}

export function isScrollToRowMessage(msg: any): msg is ScrollToRowMessage {
    return (
        msg &&
        msg.type === "scrollToRow" &&
        typeof msg.position === "number"
    );
}

export type EditorMessage = NavigateToSheetMessage | FocusWindowMessage | ScrollToRowMessage;
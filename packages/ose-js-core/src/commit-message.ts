import type {ChangeRecord, UpdateChangeRecord, AddChangeRecord, DeleteChangeRecord} from "./model";
import {COLUMN_NAMES} from "./constants";

export interface CommitMessageResult {
    title: string;
    description: string;
}

interface RowAccumulator {
    rowId: number;
    firstAction: "change" | "add" | "delete";
    lastAction: "change" | "add" | "delete";
    originalFields: Record<string, string>;
    currentFields: Record<string, string>;
    addedFields?: Record<string, string>;
    deletedFields?: Record<string, string>;
}

function truncate(value: string, maxLen: number = 30): string {
    const clean = (value ?? "").replace(/\n/g, " ").trim();
    if (clean.length <= maxLen) return clean;
    return clean.substring(0, maxLen) + "...";
}

function rowLabel(
    rowId: number,
    fields: Record<string, string> | undefined,
    rowLookup: (rowId: number) => Record<string, any> | undefined
): string {
    const data = rowLookup(rowId) ?? fields ?? {};
    const label = data[COLUMN_NAMES.LABEL] || data["Label"] || null;
    const id = data[COLUMN_NAMES.ID] || data["ID"] || null;
    if (label && id) return `${label} (${id})`;
    if (label) return label;
    if (id) return id;
    return `Row ${rowId}`;
}

function rowLabelShort(
    rowId: number,
    fields: Record<string, string> | undefined,
    rowLookup: (rowId: number) => Record<string, any> | undefined
): string {
    const data = rowLookup(rowId) ?? fields ?? {};
    return data[COLUMN_NAMES.LABEL] || data["Label"]
        || data[COLUMN_NAMES.ID] || data["ID"]
        || `Row ${rowId}`;
}

function filterInternalFields(fields: Record<string, string>): Record<string, string> {
    const result: Record<string, string> = {};
    for (const [k, v] of Object.entries(fields)) {
        if (k !== "id") result[k] = v ?? "";
    }
    return result;
}

export function squashChanges(history: ChangeRecord[]): ChangeRecord[] {
    const accumulators = new Map<number, RowAccumulator>();

    for (const record of history) {
        const rowId = record.row;
        const existing = accumulators.get(rowId);

        if (record.type === "add") {
            const fields = filterInternalFields(record.newFields);

            if (existing && existing.firstAction === "delete") {
                existing.lastAction = "add";
                existing.currentFields = {...fields};
            } else {
                accumulators.set(rowId, {
                    rowId,
                    firstAction: "add",
                    lastAction: "add",
                    originalFields: {},
                    currentFields: {...fields},
                    addedFields: {...fields},
                });
            }
        } else if (record.type === "delete") {
            const fields = filterInternalFields(record.oldFields);

            if (existing) {
                existing.lastAction = "delete";
                existing.deletedFields = {...fields};
            } else {
                accumulators.set(rowId, {
                    rowId,
                    firstAction: "delete",
                    lastAction: "delete",
                    originalFields: {...fields},
                    currentFields: {},
                    deletedFields: {...fields},
                });
            }
        } else if (record.type === "change") {
            if (existing) {
                for (const [k, v] of Object.entries(record.oldFields)) {
                    if (!(k in existing.originalFields) && existing.firstAction !== "add") {
                        existing.originalFields[k] = v ?? "";
                    }
                }
                for (const [k, v] of Object.entries(record.newFields)) {
                    existing.currentFields[k] = v ?? "";
                }
                existing.lastAction = "change";
            } else {
                const origFields: Record<string, string> = {};
                for (const [k, v] of Object.entries(record.oldFields)) {
                    origFields[k] = v ?? "";
                }
                const currFields: Record<string, string> = {};
                for (const [k, v] of Object.entries(record.newFields)) {
                    currFields[k] = v ?? "";
                }

                accumulators.set(rowId, {
                    rowId,
                    firstAction: "change",
                    lastAction: "change",
                    originalFields: origFields,
                    currentFields: currFields,
                });
            }
        }
    }

    const result: ChangeRecord[] = [];

    for (const acc of accumulators.values()) {
        // Added then deleted = complete no-op
        if (acc.firstAction === "add" && acc.lastAction === "delete") {
            continue;
        }

        // Net effect is an addition
        if (acc.firstAction === "add" && acc.lastAction !== "delete") {
            result.push({type: "add", row: acc.rowId, newFields: acc.currentFields, position: 0});
            continue;
        }

        // Net effect is a deletion
        if (acc.lastAction === "delete" && acc.firstAction !== "add") {
            const fields = acc.deletedFields ?? acc.originalFields;
            result.push({type: "delete", row: acc.rowId, oldFields: fields, position: 0});
            continue;
        }

        // Net effect is an update - compute which fields actually changed
        const oldFields: Record<string, string> = {};
        const newFields: Record<string, string> = {};
        for (const field of Object.keys(acc.originalFields)) {
            const from = acc.originalFields[field] ?? "";
            const to = acc.currentFields[field] ?? from;
            if (from !== to) {
                oldFields[field] = from;
                newFields[field] = to;
            }
        }
        for (const field of Object.keys(acc.currentFields)) {
            if (!(field in acc.originalFields)) {
                oldFields[field] = "";
                newFields[field] = acc.currentFields[field] ?? "";
            }
        }

        if (Object.keys(oldFields).length === 0) {
            continue;
        }

        result.push({type: "change", row: acc.rowId, oldFields, newFields});
    }

    return result;
}

export function generateCommitMessage(
    fileName: string,
    history: ChangeRecord[],
    rowLookup: (rowId: number) => Record<string, any> | undefined
): CommitMessageResult {
    const changes = squashChanges(history);

    if (changes.length === 0) {
        return {title: `Updating ${fileName}`, description: ""};
    }

    const updates = changes.filter((c): c is UpdateChangeRecord => c.type === "change");
    const adds = changes.filter((c): c is AddChangeRecord => c.type === "add");
    const deletes = changes.filter((c): c is DeleteChangeRecord => c.type === "delete");

    const title = generateTitle(fileName, changes, updates, adds, deletes, rowLookup);
    const description = generateDescription(updates, adds, deletes, rowLookup);

    return {title, description};
}

function generateTitle(
    fileName: string,
    changes: ChangeRecord[],
    updates: UpdateChangeRecord[],
    adds: AddChangeRecord[],
    deletes: DeleteChangeRecord[],
    rowLookup: (rowId: number) => Record<string, any> | undefined
): string {
    const hasUpdates = updates.length > 0;
    const hasAdds = adds.length > 0;
    const hasDeletes = deletes.length > 0;
    const typeCount = (hasUpdates ? 1 : 0) + (hasAdds ? 1 : 0) + (hasDeletes ? 1 : 0);

    if (typeCount === 1) {
        const first = changes[0];
        if (!first) return `Updating ${fileName}`;

        if (hasUpdates && updates.length === 1 && first.type === "change") {
            const fields = Object.keys(first.newFields);
            if (fields.length === 1 && fields[0]) {
                const candidate = `Update ${fields[0]} of ${rowLabelShort(first.row, first.newFields, rowLookup)} in ${fileName}`;
                if (candidate.length <= 72) return candidate;
            }
            return `Update ${rowLabelShort(first.row, first.newFields, rowLookup)} in ${fileName}`;
        }
        if (hasUpdates) {
            return `Update ${updates.length} terms in ${fileName}`;
        }
        if (hasAdds && adds.length === 1 && first.type === "add") {
            return `Add ${rowLabelShort(first.row, first.newFields, rowLookup)} to ${fileName}`;
        }
        if (hasAdds) {
            return `Add ${adds.length} terms to ${fileName}`;
        }
        if (hasDeletes && deletes.length === 1 && first.type === "delete") {
            return `Delete ${rowLabelShort(first.row, first.oldFields, rowLookup)} from ${fileName}`;
        }
        if (hasDeletes) {
            return `Delete ${deletes.length} terms from ${fileName}`;
        }
    }

    const parts: string[] = [];
    if (hasUpdates) parts.push(`update ${updates.length}`);
    if (hasAdds) parts.push(`add ${adds.length}`);
    if (hasDeletes) parts.push(`delete ${deletes.length}`);

    return `Edit ${fileName}: ${parts.join(", ")}`;
}

const MAX_DESCRIPTION_LINES = 50;

function generateDescription(
    updates: UpdateChangeRecord[],
    adds: AddChangeRecord[],
    deletes: DeleteChangeRecord[],
    rowLookup: (rowId: number) => Record<string, any> | undefined
): string {
    const lines: string[] = [];

    if (updates.length > 0) {
        lines.push("Updated terms:");
        for (const u of updates) {
            if (lines.length >= MAX_DESCRIPTION_LINES) break;
            const ref = rowLabel(u.row, u.newFields, rowLookup);
            const fieldDescs = Object.keys(u.oldFields).map(field =>
                `${field}: "${truncate(u.oldFields[field] ?? "")}" -> "${truncate(u.newFields[field] ?? "")}"`
            );
            lines.push(`- ${ref}: ${fieldDescs.join(", ")}`);
        }
        lines.push("");
    }

    if (adds.length > 0) {
        lines.push("Added terms:");
        for (const a of adds) {
            if (lines.length >= MAX_DESCRIPTION_LINES) break;
            lines.push(`- ${rowLabel(a.row, a.newFields, rowLookup)}`);
        }
        lines.push("");
    }

    if (deletes.length > 0) {
        lines.push("Deleted terms:");
        for (const d of deletes) {
            if (lines.length >= MAX_DESCRIPTION_LINES) break;
            lines.push(`- ${rowLabel(d.row, d.oldFields, rowLookup)}`);
        }
        lines.push("");
    }

    const total = updates.length + adds.length + deletes.length;
    if (lines.length >= MAX_DESCRIPTION_LINES) {
        lines.push(`... and more changes (${total} total)`);
    }

    while (lines.length > 0 && lines[lines.length - 1] === "") {
        lines.pop();
    }

    return lines.join("\n");
}

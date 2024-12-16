import {ref, Ref} from "vue";
import {ChangeRecord} from "../common/model.ts";

export interface Updatable {
    updateData(updates: ({ id: number } & Record<string, any>)[]): unknown,

    addData(data: ({ id: number } & Record<string, any>)[], top?: boolean, before?: number): unknown,

    deleteRow(id: number): unknown

}

export class HistoryService {

    private readonly _folder: string;
    private readonly _fileName: string;
    private readonly _repo: string

    public constructor(folder: string, fileName: string, repo: string) {
        this._folder = folder;
        this._fileName = fileName;
        this._repo = repo;

        this._history = ref([])
        this._future = ref([])
    }

    private _history: Ref<ChangeRecord[]>;

    public get history(): ChangeRecord[] {
        return this._history.value;
    }

    private _future: Ref<ChangeRecord[]>;

    public get future(): ChangeRecord[] {
        return this._future.value;
    }

    public canRedo(): boolean {
        return this._future.value.length > 0;
    }

    public canUndo(): boolean {
        return this._history.value.length > 0;
    }

    public canRestoreChanges(): boolean {
        return this.storedHistory().length > 0
    }

    public storedHistory(): ChangeRecord[] {
        const stored = localStorage.getItem(this.storageKey("history"));
        return stored ? JSON.parse(stored) : [];
    }

    public storedFuture(): ChangeRecord[] {
        const stored = localStorage.getItem(this.storageKey("future"));
        return stored ? JSON.parse(stored) : [];
    }

    public clear() {
        this._future.value = []
        this._history.value = []

        this.backupChanges();
    }

    public backupChanges() {
        const history = JSON.stringify(this._history.value);
        localStorage.setItem(this.storageKey("history"), history);
        const future = JSON.stringify(this._future.value);
        localStorage.setItem(this.storageKey("future"), future);
    }

    public restoreChanges(table: Updatable) {
        const jsonHistory = localStorage.getItem(this.storageKey("history"));
        this._history.value = JSON.parse(jsonHistory ?? "[]");
        const jsonFuture = localStorage.getItem(this.storageKey("future"))
        this._future.value = JSON.parse(jsonFuture ?? "[]");

        for (const change of this._history.value) {
            if (change.type === "change") {
                table.updateData([{id: change.row, ...change.newFields}])
            } else if (change.type === "delete") {
                table.deleteRow(change.row)
            } else if (change.type === "add") {
                table.addData([{id: change.row, ...change.newFields}], true, change.position)
            }
        }
    }

    public recordChange(value: Record<string, any>, oldValue: Record<string, any>, rowPosition: number, columnName: string): void
    public recordChange(value: string, oldValue: string, rowPosition: number, columnName: string): void
    public recordChange<T extends string | Record<string, any>>(value: T, oldValue: T, rowPosition: number, columnName: string): void {
        const changeRecord: ChangeRecord = {
            type: "change",
            row: rowPosition,
            newFields: typeof value === "string" ? {
                [columnName]: value
            } : value,
            oldFields: typeof oldValue === "string" ? {
                [columnName]: oldValue
            } : oldValue
        }

        this._history.value.push(changeRecord)

        this._future.value = []

        this.backupChanges();
    }

    public recordRowAdded(id: number, position: number, values: Record<string, any> = {}) {
        this._history.value?.push({type: "add", row: id as number, position, newFields: values})

        this._future.value = []

        this.backupChanges();
    }

    public recordRowDeleted(id: number, position: number, data: Record<string, any>) {
        this._history.value?.push({type: "delete", row: id as number, position, oldFields: {...data}})

        this._future.value = []

        this.backupChanges();
    }

    public undo(table: Updatable, steps: number = 1) {
        let result = false;
        let change: ChangeRecord | undefined;
        for (change = this._history.value.pop(); change && steps !== 0; steps--) {
            if (change?.type === "change") {
                table.updateData([{id: change.row, ...change.oldFields}])
                this._future.value.push(change)

                result = true;
            } else if (change?.type === "delete") {
                table.addData([{id: change.row, ...change.oldFields}], true, change.position)
                this._future.value.push(change)

                result = true;
            } else if (change?.type === "add") {
                table.deleteRow(change.row)
                this._future.value.push(change)

                result = true;
            }
        }

        this.backupChanges()

        return result;
    }

    public redo(table: Updatable, steps: number = 1) {
        let result = false;
        let change: ChangeRecord | undefined;
        for (change = this._future.value.pop(); change && steps !== 0; steps--) {
            if (change?.type === "change") {
                table.updateData([{id: change.row, ...change.newFields}])
                this._history.value.push(change)

                result = true;
            } else if (change?.type === "delete") {
                table.deleteRow(change.row);
                this._history.value.push(change)

                result = true;
            } else if (change?.type === "add") {
                table.addData([{id: change.row, ...change.newFields}], true, change.position)
                this._history.value.push(change)

                result = true;
            }
        }

        this.backupChanges()

        return result;
    }

    private storageKey(subkey: string) {
        return `history_${this._repo}_${this._folder}_${this._fileName}_${subkey}`
    }

}

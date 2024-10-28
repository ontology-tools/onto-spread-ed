import {COLUMN_NAMES, CURATION_STATUS} from "./constants.ts";
import {ColumnDefinition, RowComponent, Tabulator} from "tabulator-tables";


export function setRowColor(row: RowComponent, data, navigateToRow: number = -1) {
    const curation_status = data[COLUMN_NAMES.CURATION_STATUS]?.toLowerCase().replace(/\s+/g, '') ?? null

    if (curation_status !== null) {
        for (let status of Object.values(CURATION_STATUS)) {
            if (curation_status.indexOf(status.toLowerCase()) !== -1) {
                // Remove all other curation status css classes
                for (const c of row.getElement().classList) {
                    if (c.startsWith(`ose-curation-status-`)) {
                        row.getElement().classList.remove(c);
                    }
                }
                // Add curation status css class
                row.getElement().classList.add(`ose-curation-status-${status.toLowerCase()}`)
            }
        }
    }

    if (navigateToRow === row.getIndex()) {
        row.getElement().style.boxShadow = "inset 0 0 10px 5px #ffcb00"
    }
}


const headerMenuFactory = (table: () => Tabulator) => [
    {
        label: "Hide Column",
        action: function (e, column: ColumnDefinition) {
            column.hide();
        }
    },
    {
        label: "Show Hidden",
        action: function (e, column: ColumnDefinition) {
            console.log(table)
            const allColumns = table().getColumns();
            for (const column of allColumns) {
                column.show()
            }
        }
    },
    {
        label: "Reset All Column Widths",
        action: function (e, column) {
            const allColumns = table().getColumns();
            for (const column of allColumns) { //don't re-size checkbox column (column 0)
                //"E-CigO" and "Fuzzy set" are a different size
                if (column.getField() == "E-CigO" || column.getField() == "Fuzzy set") {
                    column.setWidth(140);
                } else {
                    column.setWidth(200);
                }
            }
        }
    },
]


export function columnDefFor(fieldName: string, table: () => Tabulator): ColumnDefinition {
    const headerMenu = headerMenuFactory(table);
    const TODO_suggestValuesArray = ["Test A", "Test B"]
    if (fieldName == COLUMN_NAMES.CURATION_STATUS) {
        return ({
            title: fieldName,
            field: fieldName,
            sorter: "string",
            editor: "list",
            editable: true,
            editorParams: {values: ["Pre-proposed", "Proposed", "To Be Discussed", "In Discussion", "Discussed", "Published", "Obsolete"]},
            headerFilter: "input",
            width: "200",
            formatter: "textarea",
            headerMenu
        });
    } else if (fieldName == "E-CigO") {
        return ({
            title: fieldName,
            field: fieldName,
            sorter: "boolean",
            hozAlign: "center",
            editor: true,
            formatter: "tickCross",
            headerFilter: true,
            width: "140",
            headerMenu
        });
    } else if (fieldName == "Fuzzy set") {
        return ({
            title: fieldName,
            field: fieldName,
            sorter: "boolean",
            hozAlign: "center",
            editor: true,
            formatter: "tickCross",
            headerFilter: true,
            width: "140",
            headerMenu
        });
    } else if (fieldName == "To be reviewed by") {
        return ({
            title: fieldName,
            field: fieldName,
            sorter: "string",
            editor: "textarea",
            editable: true,
            headerFilter: "input",
            width: "200",
            formatter: "textarea",
            headerMenu
        });
    } else if (fieldName == "Parent") {
        //  return({ title: fieldName, field: fieldName, sorter: "string", editor: "autocomplete", editorParams: { values: TODO_suggestValuesArray, freetext: true, allowEmpty: true }, editable: true, headerFilter: "input", width: "200", formatter: "textarea", headerMenu: HEADER_MENU });
        return ({
            title: fieldName,
            field: fieldName,
            sorter: "string",
            editor: "list",
            editorParams: {
                values: TODO_suggestValuesArray,
                autocomplete: true,
                freetext: true,
                allowEmpty: true,
                // elementAttributes: {formatter: "textarea"},
            },
            editable: true,
            headerFilter: "input",
            width: "200",
            formatter: "textarea",
            headerMenu
        });
    } else if (fieldName.includes("REL") || fieldName === "Domain" || fieldName === "Range") {
        return ({
            title: fieldName,
            field: fieldName,
            sorter: "string",
            editor: "list",
            editorParams: {
                values: TODO_suggestValuesArray,
                autocomplete: true,
                freetext: true,
                allowEmpty: true,
                // elementAttributes: {formatter: "textarea"},
            },
            editable: true,
            headerFilter: "input",
            width: "200",
            formatter: "textarea",
            headerMenu
        });
    } else {
        return ({
            title: fieldName,
            field: fieldName,
            sorter: "string",
            editor: "textarea",
            editable: true,
            headerFilter: "input",
            width: "200",
            formatter: "textarea",
            headerMenu
        });
    }
}

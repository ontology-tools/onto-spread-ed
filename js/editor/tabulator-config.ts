import {COLUMN_NAMES, CURATION_STATUS} from "./constants.ts";
import {ColumnDefinition} from "tabulator-tables";

export const CURATION_STATUS_COLORS = {
    [CURATION_STATUS.DISCUSSED]: 'moccasin',
    [CURATION_STATUS.PROPOSED]: '#FFFFFF',
    [CURATION_STATUS.TO_BE_DISCUSSED]: '#eee8aa',
    [CURATION_STATUS.IN_DISCUSSION]: '#fffacd',
    [CURATION_STATUS.PUBLISHED]: '#7fffd4',
    [CURATION_STATUS.OBSOLETE]: '#2f4f4f',
    [CURATION_STATUS.EXTERNAL]: '#D3D3D3',
    [CURATION_STATUS.PRE_PROPOSED]: '#ebfad0'
}

export function setRowColor(row, data, navigateToRow: number = -1) {
    const curation_status = data[COLUMN_NAMES.CURATION_STATUS]?.toLowerCase().replace(/\s+/g, '') ?? null

    if (curation_status !== null) {
        if (!row.isSelected()) {
            for (let status in CURATION_STATUS_COLORS) {

                if (curation_status.indexOf(status.toLowerCase()) !== -1) {
                    row.getElement().style.backgroundColor = CURATION_STATUS_COLORS[status]; //apply css change to row element
                }
            }
        } else {
            row.getElement().style.backgroundColor = 'grey'; //replaced select highlighting here!
        }
    }

    if (navigateToRow === row.getIndex()) {
        row.getElement().style.boxShadow = "inset 0 0 10px 5px #ffcb00"
    }
}


const HEADER_MENU = [
    {
        label: "Hide Column",
        action: function (e, column) {
            column.hide();
        }
    },
    {
        label: "Show Hidden",
        action: function (e, column) {
            var allColumns = table.getColumns();
            for (var i = 0; i < allColumns.length; i++) {
                if (!table.getColumn(allColumns[i]).isVisible()) {
                    table.getColumn(allColumns[i]).show();
                }
            }
        }
    },
    {
        label: "Reset All Column Widths",
        action: function (e, column) {
            var allColumns = table.getColumns();
            for (var i = 1; i < allColumns.length; i++) { //don't re-size checkbox column (column 0)
                //"E-CigO" and "Fuzzy set" are a different size
                if (table.getColumn(allColumns[i]).getField() == "E-CigO" || table.getColumn(allColumns[i]).getField() == "Fuzzy set") {
                    table.getColumn(allColumns[i]).setWidth(140);
                } else {
                    table.getColumn(allColumns[i]).setWidth(200);
                }
            }
        }
    },
]


export function columnDefFor(fieldName: string): ColumnDefinition {
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
            headerMenu: HEADER_MENU
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
            headerMenu: HEADER_MENU
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
            headerMenu: HEADER_MENU
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
            headerMenu: HEADER_MENU
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
            headerMenu: HEADER_MENU
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
            headerMenu: HEADER_MENU
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
            headerMenu: HEADER_MENU
        });
    }
}

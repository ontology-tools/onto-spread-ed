import {CellComponent, ColumnComponent, RowComponent} from "tabulator-tables";

/**
 * Same as `RowComponent.getCell` but returns `null` instead of `false` when the column does not exist.
 *
 * Returning `null` allows usage with the optional chaining operator `?.`
 *
 * @param row
 * @param column
 */
export function getCell(row: RowComponent, column: string | HTMLElement | ColumnComponent): CellComponent | null {
    const ret = row.getCell(column);
    return ret ? ret : null;
}


export interface SpreadsheetData<RowType = Record<string, string | null | number | boolean>> {
  header: string[],
  rows: RowType[],
  file_sha: string,
  repo_name: string,
  folder: string,
  spreadsheet_name: string,
}

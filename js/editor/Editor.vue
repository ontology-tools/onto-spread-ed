<script lang="ts" setup>
import {computed, h, onMounted, onUnmounted, ref, watch, watchEffect} from 'vue';
import {RowComponent, TabulatorFull as Tabulator} from 'tabulator-tables';
import {columnDefFor, setRowColor} from "./tabulator-config.ts"
import {COLUMN_NAMES, CURATION_STATUS} from "./constants.ts";
import {alertDialog, confirmDialog, promptDialog} from "../common/bootbox"
import {ChangeRecord, Diagnostic as DiagnosticM, RepositoryConfig} from "../common/model";
import Diagnostic from "../common/Diagnostic.vue"
import {BModal, BSpinner, BToast, BToastOrchestrator, useToastController} from "bootstrap-vue-next"
import {DIAGNOSTIC_DATA} from "../common/diagnostic-data.ts";
import {debounce} from "../common/debounce.ts";

interface SpreadsheetData {
  header: string[],
  rows: Record<string, string | null | number | boolean>[],
  file_sha: string,
  repo_name: string,
  folder: string,
  spreadsheet_name: string,
}

declare var URLS: { [key: string]: any };
declare var ALL_INITIALS: string[];
declare var LOGIN_INITIALS: string;
declare var REPOSITORY_CONFIG: RepositoryConfig;
const URL_PREFIX = URLS['prefix'];

const {show: showToast, remove: removeToast} = useToastController()

const table = ref<HTMLDivElement | null>(null); //reference to your table element
const tabulator = ref<Tabulator | null>(null); //variable to hold your table
// const tableData = reactive([]); //data for table to display
const spreadsheetData = ref<SpreadsheetData | null>(null);
const tableData = computed(() => spreadsheetData.value?.rows?.map((r, i) => ({
  id: i,
  ...r
})) ?? [])
const tableColumns = computed(() => spreadsheetData.value?.header?.map(h => columnDefFor(h, () => tabulator.value)))
const path = location.pathname.split('/edit/')[1];
const repo = path.substring(0, path.indexOf("/"));
const filePath = path.substring(path.indexOf("/") + 1);
const fileName = filePath.split('/').at(-1)
const fileFolder = filePath.substring(0, filePath.lastIndexOf("/"))
const tableBuilt = ref<boolean>(false);
const selectedRows = ref<RowComponent[]>([]);

const showDiagnosticList = ref<boolean>(false);

const filterToDiagnostics = ref<("error" | "warning" | "info")[]>([]);

const changes = ref<ChangeRecord[]>([])
const changed = computed(() => changes.value.length > 0)

// Submit fields
const submitCommitMessage = ref<string>(`Updating ${fileName}`);
const submitDetailedMessage = ref<string>("");

// Generic flag to lock the UI
const lock = ref<boolean>(false);
const saving = ref<boolean>(false);
const verifying = ref<boolean>(false);
const locked = computed(() => lock.value || !tableBuilt || saving.value || verifying.value)

const valid = computed(() => errors.value.length <= 0 && warnings.value.length <= 0);

const saveDialogOpen = ref<boolean>(false);

const diagnostics = ref<{
  [k: number]: { type: "error" | "warning" | "info", diagnostic: DiagnosticM, _id: number }[]
}>({});
const allDiagnostics = computed(() => Object.values(diagnostics.value).flatMap(x => x).sort((a, b) => a.diagnostic.row - b.diagnostic.row));
const errors = computed(() => allDiagnostics.value.filter(x => x.type === "error"));
const warnings = computed(() => allDiagnostics.value.filter(x => x.type === "warning"));
const infos = computed(() => allDiagnostics.value.filter(x => x.type === "info"));


const onWindowSizeChanged = debounce(() => {
  if (!tableBuilt.value) {
    return;
  }

  tabulator.value?.setHeight(document.querySelector(".row.editor-row")?.getBoundingClientRect()?.height ?? 400)
})

onMounted(() => {
  loadData()
  window.addEventListener("resize", onWindowSizeChanged);
})
onUnmounted(() => {
  window.removeEventListener("resize", onWindowSizeChanged);
})

watch(showDiagnosticList, () => {
  onWindowSizeChanged();
})

watchEffect(() => {
  if (spreadsheetData.value !== null && tabulator.value === null) {
    //instantiate Tabulator when element is mounted
    const instance = new Tabulator(table.value!, {
      data: tableData.value, //link data to table
      reactiveData: true, //enable data reactivity
      columns: tableColumns.value, //define table columns
      columnDefaults: {
        tooltip(_, cell) {
          const messages = diagnostics.value[cell.getRow().getData()["id"]] ?? []

          if (messages.length === 0) {
            return "";
          }

          function diagnosticHTML(d: { type: "error" | "warning" | "info", diagnostic: DiagnosticM, _id: number }) {
            const badgeClass = d.type === 'error' ? 'danger' : d.type
            return `<li><span class="badge text-bg-${badgeClass}" style="text-transform: capitalize">${d.type}</span>
                      ${DIAGNOSTIC_DATA[d.diagnostic.type].message(d.diagnostic)}</li>`;
          }

          return `<ul style="list-style: none">${messages.map(diagnosticHTML).join("\n")}</ul>`
        },
      },
      groupToggleElement: "header",
      nestedFieldSeparator: "|>",
      layout: "fitColumns",
      movableRows: false,
      groupBy: "Id",
      groupStartOpen: true,
      persistence: true,
      history: true, //records table interaction
      scrollToRowPosition: "bottom", //for scrollToRow()
      scrollToRowIfVisible: false, //don't scroll if row already on screen
      height: document.querySelector(".row.editor-row")?.scrollHeight,
      selectableRows: "highlight",
      rowHeader: {
        formatter: "rowSelection",
        titleFormatter: "rowSelection",
        headerSort: false,
        resizable: false,
        frozen: true,
        headerHozAlign: "center",
        hozAlign: "center"
      },

      //highlight on load table:
      rowFormatter: (row: RowComponent) => {
        const data = row.getData();

        setRowColor(row, data);

        if (data[COLUMN_NAMES.CURATOR]?.indexOf(LOGIN_INITIALS) >= 0) {
          row.getElement().classList.add("assigned-to-me")
        } else {
          row.getElement().classList.remove("assigned-to-me")
        }

        row.getElement().classList.remove("has-error", "has-warning", "changed")
        row.getCells().forEach(c => c.getElement().classList.remove("has-error", "has-warning", "changed"))

        for (const change of changes.value) {
          if (change.row === row.getPosition() as number) {
            if (change.type === "add") {
              row.getElement().classList.add("changed")
            } else if (change.type === "change") {
              for (const field in change.fields) {
                row.getCell(field)?.getElement()?.classList?.add("changed")
              }
            }
          }
        }

        const messages = diagnostics.value?.[data?.id] ?? []
        for (const message of messages) {
          const d = message.diagnostic
          if (d.type.match(/-parent/)) {
            row.getCell("Parent")?.getElement()?.classList?.add(`has-${message.type}`)
          } else if (d.type.match(/-label/)) {
            row.getCell("Label")?.getElement()?.classList?.add(`has-${message.type}`)
          } else if (d.type.match(/-id/)) {
            row.getCell("ID")?.getElement()?.classList?.add(`has-${message.type}`)
          } else if (d.type.match(/-relation-value/)) {
            row.getCell(`REL '${d.relation?.label}'`)?.getElement()?.classList?.add(`has-${message.type}`)
          } else {
            row.getElement().classList.add(`has-${message.type}`)
          }
        }
      },
    });

    // Update reactive properties manually on change
    instance.on("tableBuilt", () => {
      tableBuilt.value = true;
      validate();
    })
    instance.on("rowSelectionChanged", (_, selected) => selectedRows.value = selected)
    // instance.on("rowSelected", row => {
    //   console.trace("Not implemented")
    // });
    // instance.on("rowDeselected", row => {
    //   console.trace("Not implemented")
    // });
    // instance.on("cellEditing", cell => {
    //   console.trace("Not implemented")
    // });
    instance.on("cellEdited", async cell => {
      recordChange(cell.getValue(), cell.getRow().getPosition() as number, cell.getColumn().getField())
    });
    // instance.on("cellEditCancelled", cell => {
    //   console.trace("Not implemented")
    // });
    instance.on("dataChanged", _ => {
      // validate()
    });
    instance.on("rowAdded", row => {
      changes.value?.push({type: "add", row: row.getPosition() as number, fields: {}})
    });
    instance.on("rowDeleted", row => {
      changes.value?.push({type: "delete", row: row.getPosition() as number, fields: {}})
    });

    tabulator.value = instance;
  }
})

watchEffect(() => {
  if (tabulator.value === null || !tableBuilt.value) {
    return
  }

  tabulator.value.setFilter(row => filterToDiagnostics.value.length === 0 || !!diagnostics.value[row["id"]]?.find(d => filterToDiagnostics.value.includes(d.type)))
})

async function validateImmediate() {
  verifying.value = true;
  const toast = showToast?.({
    props: {
      value: true,
    },
    component: h(BToast, null, {
      default: () => h("div", {style: "display: flex; align-items: center; gap: 16px"}, [
        h("div", {class: "spinner-border text-primary spinner-border-sm"}),
        "Validating ..."
      ])
    })
  })!;
  const rows = tabulator?.value?.getData();

  if (!rows) {
    return;
  }

  const data = {
    repository: REPOSITORY_CONFIG.short_name,
    spreadsheet: filePath,
    rows
  }

  try {

    const response = await fetch(`${URL_PREFIX}/api/validate/file`, {
      method: "POST",
      headers: {
        "Content-type": "application/json",
        "Accept": "application/json"
      },
      body: JSON.stringify(data)
    })

    const result = await response.json();

    diagnostics.value = {}
    for (const error of result.errors) {
      if (!diagnostics.value[error.row - 2]) {
        diagnostics.value[error.row - 2] = []
      }

      diagnostics.value[error.row - 2].push({type: 'error', diagnostic: error, _id: -1})
    }

    for (const warning of result.warnings) {
      if (!diagnostics.value[warning.row - 2]) {
        diagnostics.value[warning.row - 2] = []
      }

      diagnostics.value[warning.row - 2].push({type: 'warning', diagnostic: warning, _id: -1})
    }

    allDiagnostics.value.forEach((d, i) => {
      d["_id"] = i
    })

    tabulator.value?.getRows()?.forEach(r => r.reformat())

    removeToast?.(toast);

    if (valid.value) {
      showToast?.({
        props: {
          value: 5000,
          progressProps: {
            variant: 'success',
          }
        },
        component: h(BToast, {variant: "success"}, {
          default: () => h("div", {style: "display: flex; align-items: center; gap: 16px"}, [
            h("i", {class: "fa fa-check"}),
            h("span", null, "No errors found!")
          ])
        })
      })
    } else if (errors.value.length > 0) {
      showToast?.({
        props: {
          value: 5000,
          progressProps: {
            variant: 'danger',
          }
        },
        component: h(BToast, {variant: "danger"}, {
          default: () => h("div", {style: "display: flex; align-items: center; gap: 16px"}, [
            h("i", {class: "fa fa-circle-xmark"}),
            h("span", null, `${errors.value.length} errors and ${warnings.value.length} warnings found`)
          ])
        })
      })
    } else {
      showToast?.({
        props: {
          value: 5000,
          progressProps: {
            variant: 'warning',
          }
        },
        component: h(BToast, {variant: "warning"}, {
          default: () => h("div", {style: "display: flex; align-items: center; gap: 16px"}, [
            h("i", {class: "fa fa-triangle-exclamation"}),
            h("span", null, `${warnings.value.length} warnings found`)
          ])
        })
      })
    }

    showDiagnosticList.value = !valid.value;
  } catch {
    removeToast?.(toast);
    showToast?.({
      props: {
        value: 5000,
        progressProps: {
          variant: 'danger',
        }
      },
      component: h(BToast, {variant: "danger"}, {
        default: () => h("div", {style: "display: flex; align-items: center; gap: 16px"}, [
          h("i", {class: "fa fa-triangle-exclamation"}),
          h("span", null, `Problem communicating with the server`)
        ])
      })
    })
  }

  verifying.value = false;
}

const validate = debounce(() => validateImmediate());

async function loadData() {
  console.log({repo, filePath})
  const response = await (await fetch(`${URL_PREFIX}/api/edit/get/${repo}/${filePath}`)).json()

  if (!response.success) {
    await alertDialog({
      title: "Failed to load data",
      message: `The spreadsheet '${filePath}' could not be loaded: ${response.error}`
    })
  } else {
    console.log(response.spreadsheet)
    spreadsheetData.value = response.spreadsheet;
  }
}

async function scrollAndHighlightRow(position: number) {
  const row = tabulator.value?.getRowFromPosition(position);
  await row?.scrollTo("center", true)

  row?.getElement().classList.add("highlight");
  await new Promise(r => setTimeout(r, 3000))
  row?.getElement().classList.remove("highlight");
}


/************* UTILITY FROM OLD ****************/

function saveCurator(row: RowComponent) {
  //if a field in any column except "Curator" edited
  //check "Curator" column for loginInitials and auto fill
  const data = row.getData();

  if (data[COLUMN_NAMES.CURATOR] !== undefined) { // if curator column present in table
    const cellValue: string = data[COLUMN_NAMES.CURATOR];
    const curators = [...cellValue?.split(";")?.map(x => x.trim()), LOGIN_INITIALS]
        .filter((x, i, self) => !!x && self.indexOf(x) === i)
        .join("; ")
    data[COLUMN_NAMES.CURATOR] = curators;

    if (curators !== "") {
      const cellValue = data[COLUMN_NAMES.CURATOR];
      const rowValue = row.getPosition();//save absolute row position
      const columnValue = "Curator"; //column name
      recordChange(cellValue, rowValue as number, columnValue);
    }
  }
}

function recordChange(value: string, rowPosition: number, columnName: string) {
  const changeRecord: ChangeRecord = {
    type: "change",
    row: rowPosition,
    fields: {
      [columnName]: value
    }
  }

  changes.value.push(changeRecord)
}

function backupChanges() {
  const tableArray = tabulator?.value?.getData();
  //whole table:
  const jsonArray = JSON.stringify(tableArray);
  localStorage.setItem("savedTableData" + fileName, jsonArray);
  //changed cells:
  if (changes.value.length > 0) {
    const cellArray = JSON.stringify(changes);
    localStorage.setItem("savedChanges" + fileName, cellArray);
  }
}

function restoreChanges() {
  const jsonData = (localStorage.getItem("savedTableData" + fileName) ?? "") as string;
  const data = JSON.parse(jsonData);

  tabulator.value?.setData(data);

  const jsonChanges = (localStorage.getItem("savedChanges" + fileName) ?? "") as string;
  changes.value = JSON.parse(jsonChanges);

  tabulator.value?.getRows()?.forEach(r => r.reformat())
}

function clearFormatting() {
  tabulator.value?.clearSort(); // clear sorting as well
  tabulator.value?.clearFilter(true); // clear header filters       
}

function sendVisualisationRequest(filter: string[], sendType: "sheet" | "select") {
  const rows: RowComponent[] = sendType == "select" ? selectedRows.value : tabulator.value?.getRows() ?? [];

  const indices = rows.map(r => r.getIndex())
  indices.sort(function (a, b) {
    return a - b
  });

  window.open('', 'VisualisationWindow');

  const form = document.createElement("form");
  form.setAttribute("method", "post");
  form.setAttribute("action", URL_PREFIX + "/openVisualise");
  form.setAttribute("target", 'VisualisationWindow');
  const input = document.createElement('input');
  input.type = 'hidden';
  input.name = "sheet";
  input.value = filePath;
  form.appendChild(input);
  const input2 = document.createElement('input');
  input2.type = 'hidden';
  input2.name = "repo";
  input2.value = REPOSITORY_CONFIG.short_name;
  form.appendChild(input2);
  const input4 = document.createElement('input');
  input4.type = 'hidden';
  input4.name = "table";
  input4.value = JSON.stringify(tabulator?.value?.getData());
  form.appendChild(input4);
  const input5 = document.createElement('input');
  input5.type = 'hidden';
  input5.name = "indices";
  input5.value = JSON.stringify(indices);
  form.appendChild(input5);
  const input6 = document.createElement('input');
  input6.type = 'hidden';
  input6.name = "filter";
  input6.value = JSON.stringify(filter);
  form.appendChild(input6);
  document.body.appendChild(form);
  form.target = 'VisualisationWindow';
  form.submit();
  document.body.removeChild(form);
}

function saveChanges() {
  //check for validate errors:
  if (!valid.value) {
    console.log("validate errors!!!");

    const saveValidationMessage = "<ul style=\"list-style: none; padding: 0; margin: 0;\">" + allDiagnostics.value
            .map(m => `<li style="margin: 0; padding: 0; display: block"><span class="badge text-bg-${m.type === 'error' ? 'danger' : m.type}">${m.type}</span>
                            Row ${m.diagnostic.row}: ${DIAGNOSTIC_DATA[m.diagnostic.type].message(m.diagnostic)}</li>`)
            .join("\n")
        + "</ul>"

    bootbox.dialog({
      title: "There are validation errors, are you sure you want to save?",
      message: saveValidationMessage,
      buttons: {
        confirm: {
          label: 'Submit anyway',
          className: 'btn-danger',
          callback: function () {
            saveDialogOpen.value = true;
          }
        },
        fix: {
          label: 'Show errors in table',
          className: 'btn-primary',
          callback: function () {
            validateButtons();
          }
        },
        cancel: {
          label: 'Cancel',
          className: 'btn-success',
        },
      }
    });
  } else {
    saveDialogOpen.value = true;
  }
}

function resetSaveDialog() {
  saveDialogOpen.value = false;
}

async function submitChanges(commitMessage: string, details: string) {
  saveDialogOpen.value = false;
  saving.value = true;

  const spreadsheet = spreadsheetData.value!;
  const rowData = JSON.stringify(tabulator.value?.getData()).replaceAll("&", "and")
  const initialData = JSON.stringify(spreadsheetData.value?.rows).replaceAll("&", "and")

  try {

    const response = await fetch(`${URL_PREFIX}/save`, {
      method: "POST",
      headers: {
        "Content-type": "application/json",
        "Accept": "application/json",
      },
      body: JSON.stringify({
        repo_key: spreadsheet.repo_name,
        file_sha: spreadsheet.file_sha,
        folder: fileFolder,
        spreadsheet: fileName,
        rowData,
        header: tabulator.value?.getColumns()?.map(c => c.getField())?.slice(1),
        initialData,
        commit_msg: commitMessage,
        commit_msg_extra: details,
        overwrite: "false" // TODO: should not be hardcoded
      })
    })

    saving.value = false;

    if (response.status === 200) {
      window.localStorage.removeItem("savedChanged" + fileName)
      changes.value = [];
      backupChanges()

      const responseData = await response.json();
      spreadsheetData.value!.file_sha = responseData['file_sha']

      showToast?.({
        props: {
          title: 'Saved!',
          body: "Changes were saved successfully to the repository.",
          value: true,
          variant: 'success',
          pos: 'top-center',

        }
      })
    } else {
      await alertDialog({
        title: `Error ${response.status}`,
        message: `<p>
                    An error occured while saving the file:
                  </p>
                  ${await response.text()}`,
        className: "danger"
      })
    }

    //
    // // console.log("request status is: " + request.status);
    // if (request.readyState === 4) {
    //   if (!request.status) {
    //     //todo: should we re-load spreadsheet like this on every successful save? 
    //     if (overwrite == 'true') { //true for merge, where there is different data to load in. 
    //       //re-load here to get updated data - need alert not bootbox (for blocking):
    //       bootbox.alert("Changes were saved successfully to the repository. Re-loading data now");
    //       tableEdited = false; //stops page from warning about unsaved changes
    //       //showSaveMessage localStorage for reload: 
    //       showSaveMessageMessage = 'Changes were saved successfully to the repository. ';
    //       localStorage.setItem("showSaveMessage" + thisSheet, showSaveMessageMessage);
    //       location.reload(true); //todo: can tabulator just update without re-loading the page? 
    //     }
    //     //for "Discussed" Curation status - need to re-load sheet to avoid new data bug
    //     if (reloadTable) { //true for "Discussed" Curation status 
    //       //re-load here to get updated data - need alert not bootbox (for blocking):
    //       bootbox.alert("Changes were saved successfully to the repository. Re-loading data now");
    //       tableEdited = false; //stops page from warning about unsaved changes
    //       //showSaveMessage localStorage for reload: 
    //       showSaveMessageMessage = 'Changes were saved successfully to the repository. ';
    //       localStorage.setItem("showSaveMessage" + thisSheet, showSaveMessageMessage);
    //       location.reload(true); //todo: can tabulator just update without re-loading the page? 
    //     }
    //     //todo: handle more error codes here and do merge in correct circumstance
    //   } else if (request.status === 400) { //repo not found error
    //     var response = JSON.parse(request.responseText);
    //     var errInfo = response['Error'];
    //     $("#saveAlert").addClass("alert-danger");
    //     $("#saveMessage").text('REPO not found - ' + errInfo);
    //     $("#saveAlert").show();
    //   } else if (request.status === 300) { //error code for merge
    //     var response = JSON.parse(request.responseText);
    //     var errInfo = response['Error'];
    //     var mergeInfo = response['merge_diff'];
    //     mergedTable = response['merged_table']
    //
    //     var conflicted = false; // not using this right now..
    //
    //     $('#saveAlert').removeClass('alert-success');
    //     $('#saveAlert').addClass('alert-danger');
    //     $("#saveMessage").append(errInfo);
    //     $("#saveMessage").append('<br> SEE THE BUTTONS ABOVE THIS MESSAGE FOR OPTIONS TO DEAL WITH THIS <br>');
    //     $("#saveMessage").append('Merge info: ' + mergeInfo);
    //     // $("#saveMessage").append('There was a problem saving changes: ' + errInfo + "--->" + mergeInfo);                                       
    //     $(".alert").alert() //???
    //     $("#saveAlert").show();
    //     $('#save-btn').hide();
    //     $("#validation-btns").hide(); //I think we don't want these here
    //     $('#updates').hide();
    //     $('#conflict-btns').show();
    //     // $("#saveMessage").text(''); //reset message
    //     // $("#saveAlert").hide();
    //     $("tr").each(function () {
    //       if ($(this).hasClass("remove")) {
    //         // console.log("REMOVE DETECTED");
    //       }
    //       if ($(this).hasClass("add")) {
    //         // console.log("ADD DETECTED");
    //       }
    //     });
    //     $("td").each(function () {
    //       if ($(this).hasClass("modify")) {
    //         // console.log("MODIFY DETECTED");
    //       }
    //       if ($(this).hasClass("conflict")) {
    //         // console.log("CONFLICT DETECTED");
    //       }
    //     });
    //     $("tr.remove").css('background-color', '#DAA520'); //orange
    //     $("tr.add").css('background-color', '#7CFC00'); //green
    //     $("td.modify").css('background-color', '#00FF00'); //lighter green
    //     $("td.conflict").css('background-color', '#FF69B4'); //hot pink //add "CONFLICT!" MESSAGE?
    //   } else if (request.status === 360) { //same as 200 only with restart to show new ID's
    //     window.localStorage.removeItem("savedChanges" + thisSheet);  //remove saved changes from localStorage
    //     bootbox.alert("Save successful - new ID's were generated.<br>The page will now refresh to load new data.");
    //     tableEdited = false; //stops page from warning about unsaved changes
    //     showSaveMessageMessage = 'Changes were saved successfully to the repository, New ID\'s have been generated';
    //     localStorage.setItem("showSaveMessage" + thisSheet, showSaveMessageMessage);
    //     location.reload(true);
    //   } else if (request.status === 403) { // No permission to save
    //     hide_save_indicator();
    //     bootbox.alert({
    //       title: "Permission denied",
    //       message: "You don't have permission to edit this file!"
    //     });
    //   } else {
    //     saveIndicator.modal('hide'); // hide save indicator if no response
    //     let errInfo;
    //     try {
    //       const response = JSON.parse(request.responseText);
    //       //console.log(response);
    //       errInfo = response['error'];
    //     } catch {
    //       errInfo = "An error occured:\n<br>" + request.responseText
    //     }
    //     $("#saveAlert").addClass("alert-danger");
    //     $("#saveMessage").append(errInfo);
    //     $("#saveAlert").show();
    //   }
    // }
  } catch (e) {
    saving.value = false;

    await alertDialog({
      title: "Connection problem",
      message: "There was a problem communicating with the server. Your changes have probably not been saved!"
    })
  }
}


/************* END UTILITY FROM OLD ****************/


const RIBBON = {
  visualiseSheet() {
    sendVisualisationRequest([], "sheet");
  },
  visualiseSelection() {
    sendVisualisationRequest([], "select");
  },
  validate() {
    validate();
  },
  saveFile() {
    saveChanges()
  },
  downloadFile() {

  },
  addRow() {
    const idNum = tabulator.value?.getDataCount() ?? 0;
    const rowObj: { id: number, [k: string]: unknown } = {id: idNum} // add to end of table! 
    for (const column of tabulator.value?.getColumns() ?? []) {
      const field = column.getField();
      rowObj[column.getField()] = "";

      switch (field?.toLowerCase()) {
        case COLUMN_NAMES.CURATION_STATUS.toLowerCase():
          rowObj[field] = CURATION_STATUS.PROPOSED;
          break;
        case COLUMN_NAMES.E_CIGO.toLowerCase():
        case COLUMN_NAMES.FUZZY_SET.toLowerCase():
          rowObj[field] = 0
          break;
        case COLUMN_NAMES.RELATIONSHIP_TYPE.toLowerCase():
          rowObj[field] = "ObjectProperty"
          break;
      }
    }

    clearFormatting(); //needs to be here, not after table.addRow or bad things happen        
    tabulator.value?.addRow(rowObj);
  },
  async deleteSelectedRows() {
    if (selectedRows.value.length > 1) {
      if (!await confirmDialog({
        title: `Delete row${selectedRows.value.length === 1 ? '' : 's'}?`,
        message: `Do you really want to delete ${selectedRows.value.length === 1 ? 'the row' : selectedRows.value.length + " rows"}?`
      })) {
        return;
      }
    }

    for (const row of selectedRows.value) {
      //if selectedRows ID column is not null and "" then don't delete!
      const data = row.getData();
      if (data[COLUMN_NAMES.ID] === undefined || data[COLUMN_NAMES.CURATION_STATUS] === undefined) {
        tabulator.value?.deleteRow(row);
      } else {
        const cell = row.getCell(COLUMN_NAMES.ID);
        if (cell.getValue().trim() !== "" && cell.getValue() !== null) { //got a defined ID - don't delete!
          //set to obsolete and show a message here
          data[COLUMN_NAMES.CURATION_STATUS] = CURATION_STATUS.OBSOLETE;

          //save change:
          const cellValue = data[COLUMN_NAMES.CURATION_STATUS];
          const rowValue = row.getPosition() as number; //save absolute row position
          const columnValue = COLUMN_NAMES.CURATION_STATUS; //column name
          recordChange(cellValue, rowValue, columnValue);

          await alertDialog({message: "You can't delete a row that has already had an ID assigned. Setting row status to 'Obsolete' instead."});
          row.deselect();

          //set initials of "Curator"
          if (COLUMN_NAMES.CURATOR in data) {
            data[COLUMN_NAMES.CURATOR] = [data[COLUMN_NAMES.CURATOR], LOGIN_INITIALS].filter(x => !!x).join("; ")
          }

          //save curator column to local storage for backup here
          //{value, row, columnName}
          //data[curator], row.getPosition(), "Curator"
          if (data[COLUMN_NAMES.CURATOR] !== "" && data[COLUMN_NAMES.CURATOR] !== null) {
            const cellValue = data[COLUMN_NAMES.CURATOR];
            const rowValue = row.getPosition() as number; //save absolute row position
            const columnValue = "Curator"; //column name
            recordChange(cellValue, rowValue, columnValue);
          }
        } else {
          // ID is "" or null, we can delete 
          tabulator.value?.deleteRow(row);
        }
      }
    }

    backupChanges();
  },
  async markAsReviewed() {
    for (let row of selectedRows.value) {
      if (row.getCell(COLUMN_NAMES.TO_BE_REVIEWED_BY) === undefined) {
        continue;
      }

      const data = row.getData();
      const cell = row.getCell(COLUMN_NAMES.TO_BE_REVIEWED_BY);
      //save "curator":
      saveCurator(row);

      const cellValue: string | undefined | null = cell.getValue();
      const reviewers = cellValue?.split(";")?.map(x => x.trim()).filter(x => x !== LOGIN_INITIALS).join("; ");
      await row.update({[COLUMN_NAMES.TO_BE_REVIEWED_BY]: reviewers});
      row.deselect(); //triggers rowDeselected()
      //backup changes

      const cellValueData = data[COLUMN_NAMES.TO_BE_REVIEWED_BY];
      const rowValue = row.getPosition() as number;//save absolute row position
      const columnValue = "To be reviewed by"; //column name
      recordChange(cellValueData, rowValue, columnValue);
    }

    backupChanges();
    tabulator.value?.redraw();
  },
  highlightOwn() {
    table.value?.classList?.toggle("highlight-assigned")
  },
  async askForReview() {
    const result = await promptDialog<string[]>({
      title: "Choose reviewers",
      inputType: 'checkbox',
      inputOptions: ALL_INITIALS.map(i => ({value: i, text: i}))
    });
    if (result === null || result.length === 0) { //cancel or no curator selected
      return;
    }

    for (const row of selectedRows.value) {
      //services:
      //1. Don't repeat initials already present
      //2. add selected initials (in dropdown) to cell
      //3. join with "; " except the first one (if cellValue !== null)

      const cell = row.getCell(COLUMN_NAMES.TO_BE_REVIEWED_BY);

      const reviewers = [cell.getValue()?.trim(), ...result].filter(x => !!x).join("; ")

      row.update({[COLUMN_NAMES.TO_BE_REVIEWED_BY]: reviewers});
      row.deselect();
      // backup changes:
      const cellValueData = reviewers;
      const rowValue = row.getPosition() as number;//save absolute row position
      const columnValue = "To be reviewed by"; //column name
      recordChange(cellValueData, rowValue, columnValue);
      backupChanges();
    }
  },
  removeFilters() {
    tabulator.value?.clearFilter(true);

  },
  showHiddenColumns() {
    const allColumns = tabulator.value?.getColumns()?.slice(1) ?? [];
    for (const column of allColumns) {
      if (!column.isVisible()) {
        column.show()
      }
    }
  },
  resetColumnWidths() {
    const allColumns = tabulator.value?.getColumns()?.slice(1) ?? [];
    for (const column of allColumns) {
      column.setWidth(defColumnSize(column.getField()));
    }
  },
  filterToErrors() {
    const cur = filterToDiagnostics.value
    filterToDiagnostics.value = cur.includes("error") ? cur.filter(x => x !== "error") : ["error", ...cur];
  },
  filterToWarnings() {
    const cur = filterToDiagnostics.value
    filterToDiagnostics.value = cur.includes("warning") ? cur.filter(x => x !== "warning") : ["warning", ...cur];
  },
  filterToInfos() {
    const cur = filterToDiagnostics.value
    filterToDiagnostics.value = cur.includes("info") ? cur.filter(x => x !== "info") : ["info", ...cur];
  }
}

function defColumnSize(field: string): number {
  const defaultColumnSize = 200;
  return {
    "e-cigo": 140,
    "fuzzy set": 140
  }[field] ?? defaultColumnSize
}


</script>

<template>
  <BToastOrchestrator/>

  <div class="editor-container">
    <div class="row mb-3">
      <div class="col-md-12">
        <div class="card p-0">
          <div class="card-body ribbon p-0 m-0">
            <div class="ribbon-full">
              <button :disabled="locked || !changed" class="btn-ribbon" @click="RIBBON.saveFile()">
                <i class="fas fa-save" style="color: cornflowerblue"></i><br>
                Save
              </button>
              <button :disabled="locked" class="btn-ribbon" @click="RIBBON.downloadFile()">
                <i class="fas fa-download" style="color: cornflowerblue"></i><br>
                Download
              </button>
            </div>
            <span class="ribbon-title" style="column-span: 2">File</span>

            <div class="ribbon-splitter"></div>

            <div class="ribbon-full">
              <button :disabled="locked" class="btn-ribbon" @click="RIBBON.addRow()">
                <i class="fas fa-plus" style="color: green"></i><br>
                Add row
              </button>

              <button :disabled="locked || selectedRows.length <= 0" class="btn-ribbon"
                      @click="RIBBON.deleteSelectedRows()">
                <i class="fas fa-trash-alt" style="color: indianred"></i><br>
                Delete
              </button>
            </div>
            <span class="ribbon-title" style="column-span: 2">Data</span>

            <div class="ribbon-splitter"></div>

            <div class="ribbon-full">
              <button :disabled="locked || selectedRows.length <= 0" class="btn-ribbon"
                      @click="RIBBON.markAsReviewed()">
                <i class="fas fa-clipboard-check" style="color: green"></i><br>
                Reviewed
              </button>
            </div>

            <span class="ribbon-title" style="grid-column: span 2">Review</span>

            <div class="ribbon-small">
              <button :disabled="locked" class="btn-ribbon" @click="RIBBON.highlightOwn()">
                <i class="fas fa-user"></i> Highlight yours
              </button>
              <button :disabled="locked || selectedRows.length <= 0" class="btn-ribbon" @click="RIBBON.askForReview()">
                <i class="fas fa-clipboard"></i> Ask for review
              </button>
            </div>


            <div class="ribbon-splitter"></div>


            <div class="ribbon-small">
              <button :disabled="locked" class="btn-ribbon" @click="RIBBON.removeFilters()">
                <i class="fas fa-filter-circle-xmark" style="color: indianred"></i> Remove filters
              </button>
              <button :disabled="locked || !!tabulator?.getColumns()?.find(c => !c.isVisible())" class="btn-ribbon"
                      @click="RIBBON.showHiddenColumns">
                <i class="fas fa-eye" style="color: cornflowerblue"></i> Show hidden columns
              </button>
              <button :disabled="locked" class="btn-ribbon" @click="RIBBON.resetColumnWidths()">
                <i class="fas fa-text-width"></i> Reset column widths
              </button>
            </div>

            <span class="ribbon-title">View</span>
            <div class="ribbon-splitter"></div>


            <div class="ribbon-small">
              <button :disabled="locked" class="btn-ribbon" @click="RIBBON.visualiseSheet()">
                <i class="fab fa-uncharted" style="color: #198754"></i> Sheet
              </button>
              <button :disabled="locked" class="btn-ribbon" @click="RIBBON.visualiseSelection()">
                <i class="fab fa-uncharted" style="color: #198754"></i> Selection
              </button>
            </div>

            <span class="ribbon-title">Visualise</span>
            <div class="ribbon-splitter"></div>


            <div class="ribbon-full">
              <button :disabled="locked" class="btn-ribbon" @click="RIBBON.validate()">
                <i class="fas fa-spell-check" style="color: orange"></i><br>
                Validate
              </button>
            </div>

            <span class="ribbon-title" style="grid-column: span 2">Validation</span>

            <div class="ribbon-splitter"></div>

            <div class="ribbon-filler"></div>
          </div>
        </div>
      </div>
    </div>

    <div class="row editor-row" :style="showDiagnosticList ? 'height: calc(100% - 200px)' : 'height: 100%'">
      <div id="contentTable" ref="table" class="table table-bordered table-hover table-sm"
           style="font-size: 0.8em; margin-bottom: 0 !important;">
      </div>
    </div>


    <button class="toggle-diagnostics bg-secondary" @click="showDiagnosticList = !showDiagnosticList"
            :style="{bottom: showDiagnosticList ? '200px' : '0'} ">
      <template v-if="showDiagnosticList">
        <i class="fa fa-chevron-down"></i> Hide validation messages
      </template>
      <template v-else>
        <i class="fa fa-chevron-up"></i> Show validation messages
      </template>
    </button>
    <div class="row border-1 border-danger overflow-scroll bg-secondary-subtle" style="height: 200px; min-height: 200px"
         v-if="showDiagnosticList">
      <div class="diagnostics-header bg-secondary">
        <button :class="{active: filterToDiagnostics.includes('error')}" :disabled="locked"
                class="btn-diagnostics-filter"
                @click="RIBBON.filterToErrors()">
          <i class="fas fa-circle-xmark" style="color: indianred"></i> Errors ({{ errors.length }})
        </button>
        <button :class="{active: filterToDiagnostics.includes('warning')}" :disabled="locked"
                class="btn-diagnostics-filter"
                @click="RIBBON.filterToWarnings()">
          <i class="fas fa-exclamation-triangle" style="color: orange"></i> Warnings ({{ warnings.length }})
        </button>
        <button :class="{active: filterToDiagnostics.includes('info')}" :disabled="locked"
                class="btn-diagnostics-filter"
                @click="RIBBON.filterToInfos()">
          <i class="fas fa-info-circle" style="color: dodgerblue"></i> Infos ({{ infos.length }})
        </button>
      </div>
      <div class="diagnostics-grid">
        <template
            v-for="d of allDiagnostics.filter(x => filterToDiagnostics.length === 0 || filterToDiagnostics.includes(x.type))">
          <i class="fa dg-type"

             :class="{'fa-circle-xmark': d.type === 'error',
                    'fa-triangle-exclamation': d.type === 'warning',
                    'fa-info-circle': d.type ==='info',
                    [`text-${d.type === 'error' ? 'danger' : d.type}`]: true}"></i>

          <a class="dg-row" @click="scrollAndHighlightRow(d.diagnostic.row - 1)" v-if="d.diagnostic.row > 0">Row
            {{ d.diagnostic.row - 1 }}</a>

          <Diagnostic :diagnostic="d.diagnostic" format="inline" class="dg-diagnostic"></Diagnostic>
        </template>
      </div>
    </div>
  </div>

  <BModal v-model="saveDialogOpen" title="Submit changes">
    <p>
      You are about to submit changes. Please describe the changes you have made to {{ fileName }}
    </p>
    <form class="form" role="form">
      <div class="form-group">
        <label for="commit-msg">Commit message</label>
        <input id="commit-msg" v-model="submitCommitMessage" class="form-control" name="commit-msg" required
               type="text">
      </div>
      <div class="form-group">
        <label for="descr">Detailed description</label>
        <textarea id="descr" v-model="submitDetailedMessage" class="form-control" name="descr">
        </textarea>
      </div>
    </form>

    <template v-slot:footer>
      <button class="btn btn-danger" @click="submitChanges(submitCommitMessage, submitDetailedMessage)">Submit</button>
      <button class="btn btn-primary" @click="resetSaveDialog()">Cancel</button>
    </template>
  </BModal>

  <BModal v-model="saving" centered
          no-close-on-backdrop no-close-on-esc no-footer no-header variant="primary">
    <p class="text-center">
      <BSpinner class="m-4" style="width: 5rem; height: 5rem;"/>
    </p>

    <h4 class="text-center">Saving file..</h4>
  </BModal>
</template>

<style lang="scss">
@use "tabulator-tables/dist/css/tabulator.min.css";
@use "tabulator-tables/dist/css/tabulator_bootstrap5.min.css";

.editor-container {
  height: calc(100vh - 143px);
  width: 100%;
  display: flex;
  flex-direction: column;

  .editor-row {
    display: flex;
    flex-flow: column;
    flex: 1 1 auto;
    overflow-y: auto;
  }

  .ribbon {
    position: relative;
    display: grid;

    grid-auto-flow: column;
    grid-auto-columns: max-content;
    grid-template-rows: 1fr 2em;

    & > * {
      margin: 0 2em;
    }

    .ribbon-base {
      grid-row: 1;

      padding: 4px;
      margin: 4px;

      button {
        background: none;
        border: none;

        &:hover:not([disabled]) {
          background: #aaaaaa;
        }

        &.active {
          background: #c8c8c8;
        }
      }

      button[disabled], button[disabled]:hover {
        i {
          color: #ccc !important;
        }
      }
    }

    .ribbon-title {
      grid-row: 2;
      margin: 0;
      padding: 0 2em;
      width: 100%;

      border-top: 1px solid grey;

      text-align: center;

      color: var(--bs-card-cap-color);
      background-color: var(--bs-card-cap-bg);
      border-top: var(--bs-card-border-width) solid var(--bs-card-border-color);
    }

    .ribbon-small {
      @extend .ribbon-base;

      align-self: start;
      display: flex;
      flex-direction: column;

      button {
        border-radius: 3px;

        display: grid;
        grid-template-columns: 20px auto;
        gap: 4px;
        justify-items: start;
        align-items: center;
      }

    }

    .ribbon-full {
      @extend .ribbon-base;

      align-self: center;
      display: flex;

      flex-direction: row;
      justify-content: center;

      button {
        padding-top: 8px;
        padding-bottom: 8px;
        border-radius: 3px;
        height: 85px;
        min-width: 85px;

        i {
          font-size: 1.5rem;
        }
      }


    }

    .ribbon-splitter {
      width: var(--bs-card-border-width);
      background: var(--bs-card-border-color);

      grid-row: 1/3;

      margin: 0;

    }

    .ribbon-filler {
      grid-row: 1/3;

    }
  }

  //grid-template-rows: auto auto auto 100%;
  //grid-auto-columns: 100%;

  .diagnostics-grid {
    margin-top: 32px;
    display: grid;
    gap: 4px 8px;
    align-items: center;
    grid-template-columns: 16px minmax(24px, auto) 1fr;
    grid-auto-rows: min-content;

    .dg-type {
      grid-column: 1
    }

    .dg-row {
      grid-column: 2;
      cursor: pointer;
    }

    .dg-diagnostic {
      grid-column: 3;
      margin-bottom: 0;
    }
  }

  .toggle-diagnostics {
    position: absolute;
    border: none;
    left: 0;
    height: 26px;
    border-radius: 5px 5px 0 0;
    padding: 0 8px;
  }

  .diagnostics-header {
    display: flex;
    height: 32px;
    margin-bottom: 4px;
    position: fixed;
  }

  .btn-diagnostics-filter {
    background: none;
    border: none;
    padding: 0 8px !important;


    &:hover:not([disabled]) {
      background: #aaaaaa;
    }

    &.active {
      background: #c8c8c8;
    }

    &[disabled], &[disabled]:hover {
      i {
        color: #ccc !important;
      }
    }
  }

  .ose-curation-status {
    &-discussed {
      background: moccasin !important;
    }

    &-proposed {
      background: #FFFFFF !important;
    }

    &-to_be_discussed {
      background: #eee8aa !important;
    }

    &-in_discussion {
      background: #fffacd !important;
    }

    &-published {
      background: #7fffd4 !important;
    }

    &-obsolete {
      background: #2f4f4f !important;
    }

    &-external {
      background: #D3D3D3 !important;
    }

    &-pre_proposed {
      background: #ebfad0 !important;
    }
  }

  .tabulator.table .tabulator-row.tabulator-selected {
    background-color: grey !important;
  }

  .tabulator.table .tabulator-row .tabulator-cell.tabulator-row-header {
    background: none !important;
  }

  .tabulator.table.highlight-assigned .assigned-to-me .tabulator-cell {
    color: black;
    font-weight: bold;
  }

  .tabulator.table .tabulator-row {
    box-shadow: inset 0 0 0 0 transparent;
    transition: box-shadow 500ms;

    &.highlight {
      box-shadow: inset 0 0 10px 5px #ffcb00;
    }
  }

  .changed {
    color: #003399;
  }


  .has-error {
    color: red !important;
    font-weight: bold;
  }

}
</style> 

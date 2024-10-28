<script setup lang="ts">
import {computed, onMounted, ref, watchEffect} from 'vue';
import {RowComponent, TabulatorFull as Tabulator} from 'tabulator-tables';
import {columnDefFor, setRowColor} from "./tabulator-config.ts"

interface SpreadsheetData {
  header: string[],
  rows: string[],
  file_sha: string,
  repo_name: string,
  folder: string,
  spreadsheet_name: string,
}

interface EditorMessage {
  dismissible: boolean,
  message: string,
  title: string,
  severity: "error" | "warning" | "success" | "info"
}

declare var URLS: { [key: string]: any }
const URL_PREFIX = URLS['prefix']

const table = ref(null); //reference to your table element
const tabulator = ref<Tabulator | null>(null); //variable to hold your table
// const tableData = reactive([]); //data for table to display
const spreadsheetData = ref<SpreadsheetData | null>(null);
const tableData = computed(() => spreadsheetData.value?.rows ?? [])
const tableColumns = computed(() => spreadsheetData.value?.header?.map(h => columnDefFor(h, () => tabulator.value)))
const filePath = location.pathname.split('/edit/')[1]
const fileName = filePath.split('/').at(-1)
const tableBuilt = ref<boolean>(false);
const selectedRows = ref<RowComponent[]>([]);

// Generic flag to lock the UI
const lock = ref<boolean>(false);
const locked = computed(() => lock.value || !tableBuilt)

const messages = ref<EditorMessage[]>([])

onMounted(() => {
  loadData()
})

watchEffect(() => {
  if (spreadsheetData.value !== null && tabulator.value === null) {
    //instantiate Tabulator when element is mounted
    const instance = new Tabulator(table.value, {
      data: tableData.value, //link data to table
      reactiveData: true, //enable data reactivity
      columns: tableColumns.value, //define table columns
      groupToggleElement: "header",
      // height: window.innerHeight / 3 * 2,
      nestedFieldSeparator: "|>",
      layout: "fitColumns",
      movableRows: false,
      groupBy: "Id",
      groupStartOpen: true,
      persistence: true,
      keybindings: true,
      history: true, //records table interaction
      virtualDomBuffer: 1500, //may be needed to fix bug where up scroll is disappearing rows
      scrollToRowPosition: "bottom", //for scrollToRow()
      scrollToRowIfVisible: false, //don't scroll if row already on screen

      selectableRows: true,
      rowHeader: {formatter: "rowSelection", titleFormatter: "rowSelection", headerSort: false, resizable: false, frozen: true, headerHozAlign: "center", hozAlign: "center"},

      //tooltips for validate:
      tooltips: true,
      tooltipGenerationMode: "hover", //update on hover
      // tooltips: function (cell) {
      //     var tooltipMsg = "ERROR - validation failed";
      //     for (var i = 0; i < validateErrorMessages.length; i += 2) {
      //         if (cell == validateErrorMessages[i]) {
      //             tooltipMsg = validateErrorMessages[i + 1]; // + (i / 2 + 1); // "+ i" just for testing
      //         }
      //     }
      //     if (cell.getElement().style.backgroundColor == 'red') {
      //         //function should return a string for the tooltip of false to hide the tooltip
      //         return tooltipMsg;
      //     } else {
      //         return false;
      //     }
      // },
      rowSelected: row => {
        console.trace("Not implemented")
      },
      rowDeselected: row => {
        console.trace("Not implemented")
      },
      rowSelectionChanged: (data, rows) => {
        this.$forceUpdate();
        console.trace("Not implemented")
      },
      cellEditing: cell => {
        console.trace("Not implemented")
      },
      cellEdited: cell => {
        console.trace("Not implemented")
      },
      cellEditCancelled: cell => {
        console.trace("Not implemented")
      },
      dataChanged: data => {
        console.trace("Not implemented")
      },
      //highlight on load table:
      rowFormatter: (row: RowComponent) => {
        const data = row.getData();

        setRowColor(row, data);

        // if (highlightLogin) {
        //     if (data[curator] === undefined) {
        //
        //     } else {
        //         if (data[curator] !== null) {
        //             var curatorA = data[curator];
        //             var nameCheckA = curatorA.indexOf(loginInitials);
        //             if (nameCheckA > -1) {
        //                 row.getElement().style.color = 'black';
        //                 row.getElement().style.fontWeight = 'bold';
        //             }
        //         }
        //     }
        // } else {
        //     row.getElement().style.color = 'black';
        //     row.getElement().style.fontWeight = 'normal';
        // }
      },
      rowAdded: row => {
        console.trace("Not implemented")
      },
      rowDeleted: row => {
        console.trace("Not implemented")
      },
    });

    // Update reactive properties manually on change
    instance.on("tableBuilt", () => tableBuilt.value = true)
    instance.on("rowSelectionChanged", (_, selected) => selectedRows.value = selected)

    tabulator.value = instance;
  }
})

function addError(message: string, title: string = "An error occurred!", dismissible: boolean = false) {
  messages.value = [...messages.value, {message, dismissible, title, severity: 'error'}]
}

async function loadData() {
  const response = await (await fetch(`${URL_PREFIX}/api/edit/get/${filePath}`)).json()

  if (!response.success) {
    console.error("Failed to load data!")
    addError(`The spreadsheet '${filePath}' could not be loaded: ${response.error}`, "Failed to load data!")
  } else {
    console.log(response.spreadsheet)
    spreadsheetData.value = response.spreadsheet;
  }
}


</script>

<template>
  <div class="editor-container">
    <div class="row mb-3">
      <div class="col-md-12">
        <h2 id="s-name"> Editing {{ fileName }} </h2>
      </div>
    </div>

    <div class="row mb-3">
      <div class="col-md-12">
        <div v-for="message in messages"
             :class="'alert alert-' + ({'error': 'danger'}[message.severity] ?? message.severity)">
          <h6 class="fw-bold">{{ message.title }}</h6>
          <p>{{ message.message }}</p>
          <button v-if="message.dismissible">Dismiss</button>
        </div>

      </div>
    </div>


    <div class="row mb-3">
      <div class="col-md-12">
        <div class="card p-0">
          <div class="card-body ribbon p-0 m-0">
            <div class="ribbon-full">
              <button class="btn-ribbon">
                <i class="fas fa-plus" style="color: green"></i><br>
                Add row
              </button>

              <button class="btn-ribbon" :disabled="locked || selectedRows.length <= 0">
                <i class="fas fa-trash-alt" style="color: indianred"></i><br>
                Delete
              </button>
            </div>
            <span class="ribbon-title" style="column-span: 2">Data</span>

            <div class="ribbon-splitter"></div>

            <div class="ribbon-full">
              <button class="btn-ribbon" :disabled="locked || selectedRows.length <= 0">
                <i class="fas fa-clipboard-check" style="color: green"></i><br>
                Reviewed
              </button>
            </div>

            <span class="ribbon-title" style="grid-column: span 2">Review</span>

            <div class="ribbon-small">
              <button class="btn-ribbon" :disabled="locked || selectedRows.length <= 0">
                <i class="fas fa-user"></i> Highlight yours
              </button>
              <button class="btn-ribbon" :disabled="locked || selectedRows.length <= 0">
                <i class="fas fa-clipboard"></i> Ask for review
              </button>
            </div>


            <div class="ribbon-splitter"></div>


            <div class="ribbon-small">
              <button class="btn-ribbon" :disabled="locked">
                <i class="fas fa-filter-circle-xmark" style="color: indianred"></i> Remove filters
              </button>
              <button class="btn-ribbon" :disabled="locked">
                <i class="fas fa-eye" style="color: cornflowerblue"></i> Show all columns
              </button>
              <button class="btn-ribbon" :disabled="locked">
                <i class="fas fa-text-width"></i> Reset column widths
              </button>
            </div>

            <span class="ribbon-title">View</span>
            <div class="ribbon-splitter"></div>


            <!--            <div class="ribbon-full">-->
            <!--              <button class="btn-ribbon">-->
            <!--                <i class="fas fa-highlighter"></i><br>-->
            <!--                Highlight-->
            <!--              </button>-->
            <!--              <button class="btn-ribbon">-->
            <!--                <i class="fas fa-chevron-down"></i>-->
            <!--              </button>-->
            <!--            </div>-->


            <div class="ribbon-filler"></div>
          </div>
        </div>
      </div>
      <!--        <div class="text-left buttons">-->
      <!--          <button id=add-row class="btn btn-outline-info btn-sm"><i class="fas fa-plus"></i> Add Row</button>-->
      <!--          <button id=delete-rows class="btn btn-outline-danger btn-sm">-->
      <!--            <i class="fas fa-trash-alt"></i> Delete Rows-->
      <!--          </button>-->
      <!--          <button id=highlight-user class="btn btn-outline-warning btn-sm">-->
      <!--            <i class="fas fa-highlighter"></i>Highlight Your Rows-->
      <!--          </button>-->
      <!--          <button id=remove-formatting class="btn btn-outline-dark btn-sm">-->
      <!--            <i class="fas fa-remove-format"></i> Remove all Filters-->
      <!--          </button>-->
      <!--          <button id=ask-for-review class="btn btn-outline-primary btn-sm">-->
      <!--            <i class="fas fa-clipboard"></i> Ask for review-->
      <!--          </button>-->
      <!--          <button id=reviewed class="btn btn-outline-primary btn-sm">-->
      <!--            <i class="fas fa-clipboard-check"></i> Reviewed-->
      <!--          </button>-->

      <!--          <div class="btn-group">-->
      <!--            <button id=visualise-sheet class="btn btn-outline-success btn-sm">-->
      <!--              <i class="fab fa-uncharted"></i> Visualise sheet-->
      <!--            </button>-->
      <!--            <button id=visualise-sheet-multiselect type="button"-->
      <!--                    class="btn btn-outline-success btn-sm dropdown-toggle dropdown-toggle-split" data-toggle="dropdown"-->
      <!--                    aria-haspopup="true" aria-expanded="false">-->
      <!--              [filter]-->
      <!--              <span class="sr-only">Toggle Dropdown</span>-->
      <!--            </button>-->
      <!--            <ul class="dropdown-menu">-->
      <!--              <li id="visualise-sheet-checkbox-list" class="dropdown">-->
      <!--                &lt;!&ndash; using jquery to add checkbox list items &ndash;&gt;-->

      <!--              </li>-->
      <!--            </ul>-->
      <!--          </div>-->

      <!--          <div class="btn-group">-->
      <!--            <button id=visualise-selection class="btn btn-outline-success btn-sm">-->
      <!--              <i class="fab fa-uncharted"></i> Visualise selection-->
      <!--            </button>-->
      <!--            <button id=visualise-selection-multiselect type="button"-->
      <!--                    class="btn btn-outline-success btn-sm dropdown-toggle dropdown-toggle-split" data-toggle="dropdown"-->
      <!--                    aria-haspopup="true" aria-expanded="false">-->
      <!--              [filter]-->
      <!--              <span class="sr-only">Toggle Dropdown</span>-->
      <!--            </button>-->
      <!--            <ul class="dropdown-menu">-->
      <!--              <li id="visualise-selection-checkbox-list" class="dropdown">-->
      <!--                &lt;!&ndash; using jquery to add checkbox list items &ndash;&gt;-->

      <!--              </li>-->
      <!--            </ul>-->
      <!--          </div>-->

      <!--          <button id=generate-identifier class="btn btn-outline-dark btn-sm">-->
      <!--            <i class="fas fa-marker"></i> Generate {{ repo_name }} identifier-->
      <!--          </button>-->

      <!--          <span class="expander"></span>-->

      <!--          <button id="save-btn" class="btn btn-outline-success btn-sm">-->
      <!--            &lt;!&ndash;              onclick="save_changes( '{{repo_name}}', '{{folder}}' , '{{ spreadsheet_name }}' , JSON.stringify( table.getData() ), JSON.stringify( testTableData ), 'false' ) "&ndash;&gt;-->
      <!--            <i class="fa fa-save"></i> Save changes to repository-->
      <!--          </button>-->
      <!--          <button id="download-sheet-btn" class="btn btn-outline-primary btn-sm">-->
      <!--            &lt;!&ndash;              onclick="download_spreadsheet( '{{repo_name}}', '{{folder}}' , '{{ spreadsheet_name }}' )"&ndash;&gt;-->
      <!--            <i class="fa fa-download"></i> Download Spreadsheet-->
      <!--          </button>-->
      <!--        </div>-->
      <!--      </div>-->
    </div>

    <div class="row editor-row" style="height: 100%">
      <div ref="table" id="contentTable" class="table table-bordered table-hover table-sm"
           style="font-size: 0.8em; height: 100%">
      </div>
    </div>
  </div>
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
        border-radius: 5px;

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

      button {
        border-radius: 5px;

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


}
</style>

<script setup lang="ts">
import {computed, onMounted, ref, watchEffect} from 'vue';
import {ColumnDefinition, TabulatorFull as Tabulator} from 'tabulator-tables';
import {setRowColor, columnDefFor} from "./tabulator-config.ts"

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
const tabulator = ref(null); //variable to hold your table
// const tableData = reactive([]); //data for table to display
const spreadsheetData = ref<SpreadsheetData | null>(null);
const tableData = computed(() => spreadsheetData.value?.rows ?? [])
const tableColumns = computed(() => spreadsheetData.value?.header?.map(h => columnDefFor(h)))
const filePath = location.pathname.split('/edit/')[1]
const fileName = filePath.split('/').at(-1)

const messages = ref<EditorMessage[]>([])

onMounted(() => {
  loadData()
})

watchEffect(() => {
  if (spreadsheetData.value !== null) {
    //instantiate Tabulator when element is mounted
    tabulator.value = new Tabulator(table.value, {
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
      rowFormatter: row => {
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
    <div class="col-md-9">
      <div class="text-left">
        <button id=add-row class="btn btn-outline-info btn-sm"><i class="fas fa-plus"></i> Add Row</button>
        <button id=delete-rows class="btn btn-outline-danger btn-sm" style="display: none"><i
            class="fas fa-trash-alt"></i> Delete
          Rows
        </button>
        <button id=highlight-user class="btn btn-outline-warning btn-sm"><i class="fas fa-highlighter"></i>
          Highlight Your Rows
        </button>
        <button id=remove-formatting class="btn btn-outline-dark btn-sm"><i class="fas fa-remove-format"></i> Remove
          all Filters
        </button>
        <button id=ask-for-review class="btn btn-outline-primary btn-sm" style="display: none"><i
            class="fas fa-clipboard"></i> Ask for
          review
        </button>
        <button id=reviewed class="btn btn-outline-primary btn-sm" style="display: none"><i
            class="fas fa-clipboard-check"></i>
          Reviewed
        </button>

        <div class="btn-group">
          <button id=visualise-sheet class="btn btn-outline-success btn-sm" style="display: none"><i
              class="fab fa-uncharted"></i>
            Visualise sheet
          </button>
          <button id=visualise-sheet-multiselect type="button"
                  class="btn btn-outline-success btn-sm dropdown-toggle dropdown-toggle-split" data-toggle="dropdown"
                  aria-haspopup="true" aria-expanded="false" style="display: none">
            [filter]
            <span class="sr-only">Toggle Dropdown</span>
          </button>
          <ul class="dropdown-menu">
            <li id="visualise-sheet-checkbox-list" class="dropdown">
              <!-- using jquery to add checkbox list items -->

            </li>
          </ul>
        </div>

        <div class="btn-group">
          <button id=visualise-selection class="btn btn-outline-success btn-sm" style="display: none"><i
              class="fab fa-uncharted"></i>
            Visualise selection
          </button>
          <button id=visualise-selection-multiselect type="button"
                  class="btn btn-outline-success btn-sm dropdown-toggle dropdown-toggle-split" data-toggle="dropdown"
                  aria-haspopup="true" aria-expanded="false" style="display: none">
            [filter]
            <span class="sr-only">Toggle Dropdown</span>
          </button>
          <ul class="dropdown-menu">
            <li id="visualise-selection-checkbox-list" class="dropdown">
              <!-- using jquery to add checkbox list items -->

            </li>
          </ul>
        </div>

        <button id=generate-identifier class="btn btn-outline-dark btn-sm" style="display: none"><i
            class="fas fa-marker"></i>
          Generate {{ repo_name }} identifier
        </button>
      </div>
    </div>

    <div class="col-md-3">
      <div class="row mb-3"></div>
      <button id="save-btn" class="btn btn-outline-success btn-sm" style="display: none">
        <!--              onclick="save_changes( '{{repo_name}}', '{{folder}}' , '{{ spreadsheet_name }}' , JSON.stringify( table.getData() ), JSON.stringify( testTableData ), 'false' ) "-->
        Save changes to repository
      </button>
      <button id="download-sheet-btn" class="btn btn-outline-primary btn-sm">
        <!--              onclick="download_spreadsheet( '{{repo_name}}', '{{folder}}' , '{{ spreadsheet_name }}' )"-->
        Download Spreadsheet
      </button>
    </div>
  </div>



<div class="row">
    <div class="col-md-12">
        <div ref="table" id="contentTable" class="table table-bordered table-hover table-sm" style="font-size: 0.8em;">
        </div>
    </div>
</div>
</template>

<style lang="scss">
  @use "tabulator-tables/dist/css/tabulator.min.css";
  @use "tabulator-tables/dist/css/tabulator_bootstrap5.min.css";
</style>

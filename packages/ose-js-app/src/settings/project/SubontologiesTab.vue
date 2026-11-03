<script lang="ts" setup>
import {Project} from "@ontospreaded/js-core";
import {promptDialog} from "../../common/bootbox";

const props = defineProps<{ project: Project }>()

async function add() {
  const name = (await promptDialog({title: "Name of the subontology", inputType: "text"}))?.trim();
  if (!name || name in props.project.subontologies) return;

  props.project.subontologies[name] = {excel_file: "", release_file: ""};
}
</script>

<template>
  <p class="text-body-secondary">
    Subontologies are used to generate the hierarchical spreadsheets. Each one consists of a spreadsheet and the
    released ontology file built from it.
  </p>

  <table v-if="Object.keys(project.subontologies).length > 0" class="table table-sm align-middle">
    <thead>
    <tr>
      <th>Name</th>
      <th>Spreadsheet</th>
      <th>Released file</th>
      <th></th>
    </tr>
    </thead>
    <tbody>
    <tr v-for="(subontology, name) in project.subontologies" :key="name">
      <td>{{ name }}</td>
      <td><input v-model="subontology.excel_file" class="form-control form-control-sm" type="text"></td>
      <td><input v-model="subontology.release_file" class="form-control form-control-sm" type="text"></td>
      <td class="text-end">
        <button class="btn btn-sm btn-outline-danger" title="Remove" type="button"
                @click="delete project.subontologies[name]">
          <i class="fa fa-trash"></i>
        </button>
      </td>
    </tr>
    </tbody>
  </table>
  <p v-else class="text-body-secondary fst-italic">No subontologies configured.</p>

  <button class="btn btn-sm btn-outline-primary" type="button" @click="add">
    <i class="fa fa-add"></i> Add subontology
  </button>
</template>

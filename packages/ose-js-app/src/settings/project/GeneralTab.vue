<script lang="ts" setup>
import {Project} from "@ontospreaded/js-core";
import KeyValueEditor from "./KeyValueEditor.vue";

const props = defineProps<{ project: Project }>()

const validationOptions = [
  {value: "include-external", label: "Include the external ontology when validating"},
  {value: "include-dependencies", label: "Include the dependencies of a file when validating"},
] as const

function toggleValidation(value: Project["validation"][number], enabled: boolean) {
  const others = props.project.validation.filter(v => v !== value);
  props.project.validation = enabled ? [...others, value] : others;
}
</script>

<template>
  <h5>Project</h5>
  <div class="row g-3 mb-4">
    <div class="col-md-4">
      <label class="form-label" for="short-name">Short name</label>
      <input id="short-name" v-model="project.short_name" class="form-control form-control-sm" type="text">
    </div>
    <div class="col-md-8">
      <label class="form-label" for="full-name">Full name</label>
      <input id="full-name" v-model="project.full_name" class="form-control form-control-sm" type="text">
    </div>
    <div class="col-md-8">
      <label class="form-label" for="iri-prefix">IRI prefix</label>
      <input id="iri-prefix" v-model="project.iri_prefix" class="form-control form-control-sm" type="text">
    </div>
    <div class="col-md-4">
      <label class="form-label" for="id-digits">ID length</label>
      <input id="id-digits" v-model.number="project.id_digits" class="form-control form-control-sm" min="1" type="number">
    </div>
  </div>

  <h5>Repository</h5>
  <div class="row g-3 mb-4">
    <div class="col-md-4">
      <label class="form-label" for="repo-short">Repository short name</label>
      <input id="repo-short" v-model="project.short_repository_name" class="form-control form-control-sm" type="text">
    </div>
    <div class="col-md-4">
      <label class="form-label" for="repo-full">GitHub repository</label>
      <input id="repo-full" :value="project.full_repository_name" class="form-control form-control-sm" disabled
             type="text">
    </div>
    <div class="col-md-4">
      <label class="form-label" for="main-branch">Main branch</label>
      <input id="main-branch" v-model="project.main_branch" class="form-control form-control-sm" type="text">
    </div>
  </div>

  <h5>Validation</h5>
  <div class="mb-4">
    <div v-for="option in validationOptions" :key="option.value" class="form-check form-switch">
      <input :id="`validation-${option.value}`" :checked="project.validation.includes(option.value)"
             class="form-check-input" role="switch" type="checkbox"
             @change="toggleValidation(option.value, ($event.target as HTMLInputElement).checked)">
      <label :for="`validation-${option.value}`" class="form-check-label">{{ option.label }}</label>
    </div>
  </div>

  <h5>Prefixes</h5>
  <p class="text-body-secondary">CURIE prefixes and the IRIs they expand to.</p>
  <KeyValueEditor :entries="project.prefixes" class="mb-4" key-label="Prefix" value-label="IRI"/>

  <h5>Read-only files</h5>
  <p class="text-body-secondary">Spreadsheets that cannot be edited, with the reason shown to the user.</p>
  <KeyValueEditor :entries="project.readonly_files" key-label="File" value-label="Reason"/>
</template>

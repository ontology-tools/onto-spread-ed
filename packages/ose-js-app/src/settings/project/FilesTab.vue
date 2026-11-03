<script lang="ts" setup>
import {computed} from "vue";
import {useRoute, useRouter} from "vue-router";
import {Project, ProjectFile} from "@ontospreaded/js-core";
import {confirmDialog, promptDialog} from "../../common/bootbox";
import KeyValueEditor from "./KeyValueEditor.vue";

const props = defineProps<{ project: Project }>()

const route = useRoute();
const router = useRouter();

const EXTERNAL = "external";

/** All files of the project by name, including the external ontology */
const files = computed<Record<string, ProjectFile>>(() => ({[EXTERNAL]: props.project.external, ...props.project.files}));

const selected = computed(() => {
  const name = route.query.file as string | undefined;
  return name !== undefined && name in files.value ? name : EXTERNAL;
});
const file = computed(() => files.value[selected.value]);

function select(name: string) {
  router.replace({query: {...route.query, file: name}});
}

/** Renames (or with `newName` null removes) a file in the `files` argument of the stages, e.g. of MERGE */
function updateStageArgs(name: string, newName: string | null) {
  for (const stage of props.project.build_configurations.flatMap(c => c.stages)) {
    const files = stage.args?.files;
    if (!Array.isArray(files)) continue;
    stage.args.files = newName === null
        ? files.filter(f => f !== name)
        : files.map(f => f === name ? newName : f);
  }
}

function normaliseName(value: string) {
  return value.trim().replace(/[ ,./\-!?=]/g, "_");
}

async function addFile() {
  const value = await promptDialog({title: "What is the name of the file?", inputType: "text"});
  if (!value) return;

  const name = normaliseName(value);
  if (name in files.value) return;

  props.project.files[name] = {
    target: {file: "", iri: "", ontology_annotations: {}, publish: true},
    sources: [],
    needs: [],
    addParentsFile: null,
    renameTermFile: null,
  };
  select(name);
}

async function renameFile(name: string) {
  const value = await promptDialog({title: "What is the name of the file?", inputType: "text", value: name});
  if (!value) return;

  const newName = normaliseName(value);
  if (newName === name || newName in files.value) return;

  // Keep the order of the files
  const entries = Object.entries(props.project.files);
  for (const [k] of entries) delete props.project.files[k];
  for (const [k, v] of entries) props.project.files[k === name ? newName : k] = v;

  for (const f of Object.values(files.value)) {
    f.needs = f.needs.map(n => n === name ? newName : n);
  }
  updateStageArgs(name, newName);
  select(newName);
}

async function deleteFile(name: string) {
  const confirmed = await confirmDialog({
    title: `Delete '${name}'`,
    message: `Do you want to remove the file ${props.project.files[name].target.file || name} from the project?`,
    buttons: {
      confirm: {label: `Delete ${name}`, className: "btn-danger"},
      cancel: {label: "Keep it", className: "btn-success"},
    },
  });
  if (!confirmed) return;

  delete props.project.files[name];
  for (const f of Object.values(files.value)) {
    f.needs = f.needs.filter(n => n !== name);
  }
  updateStageArgs(name, null);
  select(EXTERNAL);
}

// Only the files can be needed, not the external ontology
const possibleDependencies = computed(() =>
    Object.keys(props.project.files).filter(k => k !== selected.value && !file.value.needs.includes(k)));
</script>

<template>
  <div class="row">
    <div class="col-md-3 mb-3">
      <div class="list-group">
        <a v-for="(f, name) in files" :key="name" :class="{active: name === selected}"
           class="list-group-item list-group-item-action" href="#" @click.prevent="select(name as string)">
          <div class="fw-semibold">{{ name }}</div>
          <small class="file-path">{{ f.target.file || "No target file" }}</small>
        </a>
      </div>
      <button class="btn btn-sm btn-outline-primary mt-2 w-100" type="button" @click="addFile">
        <i class="fa fa-add"></i> Add file
      </button>
    </div>

    <div v-if="file" class="col-md-9">
      <div class="d-flex align-items-center gap-2 mb-3">
        <h5 class="mb-0 flex-grow-1">{{ selected }}</h5>
        <template v-if="selected !== EXTERNAL">
          <button class="btn btn-sm btn-outline-primary" type="button" @click="renameFile(selected)">
            <i class="fa fa-edit"></i> Rename
          </button>
          <button class="btn btn-sm btn-outline-danger" type="button" @click="deleteFile(selected)">
            <i class="fa fa-trash"></i> Delete
          </button>
        </template>
      </div>
      <p v-if="selected === EXTERNAL" class="text-body-secondary">
        The external ontology collects the terms imported from other ontologies.
      </p>

      <h6>Target</h6>
      <p class="text-body-secondary">
        The location of the built file in the repository and the IRI of the resulting ontology.
      </p>
      <div class="form-check form-switch mb-2">
        <input :id="`publish-${selected}`" v-model="file.target.publish" class="form-check-input" role="switch"
               type="checkbox">
        <label :for="`publish-${selected}`" class="form-check-label">Publish the file to GitHub</label>
      </div>
      <div class="input-group input-group-sm mb-2">
        <span class="input-group-text">Path</span>
        <input v-model="file.target.file" class="form-control" type="text">
      </div>
      <div class="input-group input-group-sm mb-2">
        <span class="input-group-text">IRI</span>
        <input v-model="file.target.iri" class="form-control" type="text">
      </div>
      <label class="form-label small">Ontology annotations</label>
      <KeyValueEditor :entries="file.target.ontology_annotations" class="mb-4" key-label="Annotation"/>

      <h6>Sources</h6>
      <p class="text-body-secondary">
        Spreadsheets with the terms, individuals and relations of the ontology, or previously built OWL files that are
        merged into it.
      </p>
      <div v-for="(source, i) in file.sources" :key="i" class="input-group input-group-sm mb-2">
        <span class="input-group-text">Source</span>
        <input v-model="source.file" class="form-control" type="text">
        <span class="input-group-text">Type</span>
        <select v-model="source.type" class="form-select flex-grow-0 w-auto">
          <option value="classes">Classes</option>
          <option value="relations">Relations</option>
          <option value="individuals">Individuals</option>
          <option value="owl">OWL</option>
        </select>
        <span class="input-group-text">Schema</span>
        <input v-model="source.spreadsheet_schema" class="form-control flex-grow-0 schema" type="text">
        <button class="btn btn-outline-danger" title="Remove" type="button" @click="file.sources.splice(i, 1)">
          <i class="fa fa-trash"></i>
        </button>
      </div>
      <button class="btn btn-sm btn-outline-primary mb-4" type="button"
              @click="file.sources.push({file: '', type: 'classes', spreadsheet_schema: 'default'})">
        <i class="fa fa-add"></i> Add source
      </button>

      <h6>Dependencies</h6>
      <p class="text-body-secondary">Other files that have to be loaded when building this file.</p>
      <div v-for="need in file.needs" :key="need" class="input-group input-group-sm mb-2">
        <span class="input-group-text">Dependency</span>
        <input :value="need === EXTERNAL ? need : `${need} (${files[need]?.target.file ?? 'unknown file'})`"
               class="form-control" disabled type="text">
        <button class="btn btn-outline-danger" title="Remove" type="button"
                @click="file.needs = file.needs.filter(n => n !== need)">
          <i class="fa fa-trash"></i>
        </button>
      </div>
      <select v-if="possibleDependencies.length > 0" class="form-select form-select-sm w-auto mb-4"
              @change="file.needs.push(($event.target as HTMLSelectElement).value); ($event.target as HTMLSelectElement).value = ''">
        <option disabled selected value="">Add dependency…</option>
        <option v-for="name in possibleDependencies" :key="name" :value="name">{{ name }}</option>
      </select>

      <h6>Additional files</h6>
      <div class="input-group input-group-sm mb-2">
        <span class="input-group-text">Add parents file</span>
        <input :value="file.addParentsFile ?? ''" class="form-control" type="text"
               @change="file.addParentsFile = ($event.target as HTMLInputElement).value || null">
      </div>
      <div class="input-group input-group-sm mb-2">
        <span class="input-group-text">Rename terms file</span>
        <input :value="file.renameTermFile ?? ''" class="form-control" type="text"
               @change="file.renameTermFile = ($event.target as HTMLInputElement).value || null">
      </div>
    </div>
  </div>
</template>

<style scoped>
.file-path {
  word-break: break-all;
}

.schema {
  width: 8rem;
}
</style>

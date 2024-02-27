<script setup lang="ts">
import {ReleaseScript} from "./model.ts";
import CollapsibleCard from "../common/CollapsibleCard.vue";

const props = defineProps<{
  releaseScript: ReleaseScript
}>()

function setAnnotations(name: string, annotations: string) {
  props.releaseScript.files[name].target.ontology_annotations =
      Object.fromEntries(annotations.split("\n").map(l => l.split(": ")))
}

function addDependency(name: string) {
  bootbox.prompt({
    title: `Add dependency for ${name}`,
    inputType: "select",
    inputOptions: Object.entries(props.releaseScript.files)
        .filter(([k, _]) => k != name)
        .map(([k, v]) => ({
          text: v.target.file,
          value: k
        })),
    callback(value: string) {
      if (value) {
        props.releaseScript.files[name].needs.push(value)
      }
    }
  })
}

function deleteDependency(name: string, dependency: string) {
  props.releaseScript.files[name].needs = props.releaseScript.files[name].needs.filter(x => x != dependency)
}

function addFile() {
  bootbox.prompt({
    title: `What is the name of the file?`,
    inputType: "text",
    callback(value: string) {
      if (value) {
        value = value.trim().replace(/[ ,./\-!?=]/, "_")
        props.releaseScript.files[value] = {
          target: {
            file: "",
            iri: "",
            ontology_annotations: {}
          },
          sources: [],
          needs: []
        }
      }
    }
  })
}

function renameFile(event: MouseEvent, name: string) {
  event.preventDefault();

  bootbox.prompt({
    title: `What is the name of the file?`,
    inputType: "text",
    value: name,
    callback(value: string) {
      if (value) {
        value = value.trim().replace(/[ ,./\-!?=]/, "_")
        props.releaseScript.files[value] = props.releaseScript.files[name]
        delete props.releaseScript.files[name]
      }
    }
  })
}

function deleteFile(event: MouseEvent, name: string) {

  event.preventDefault();
  bootbox.confirm({
    title: `Delete '${name}'`,
    message: `Do you want to delete the file '${name}'? It will remove the file ${props.releaseScript.files[name].target.file} from the release.`,
    buttons: {
      confirm: {
        label: `Delete ${name}`,
        className: "btn-danger",
      },
      cancel: {
        label: "Keep it",
        className: "btn-success"
      }
    },
    callback(result: boolean) {
      if (result) {
          delete props.releaseScript.files[name]
        }
    }
  })
}

</script>

<template>

  <div class="files">
    <h3>Files</h3>
    <CollapsibleCard v-for="(file, name) in releaseScript.files">
      <template #title>
        {{ name }} - {{ file.target.file }}
        <span class="badge text-bg-secondary">{{ file.sources.length }} sources</span>
        <span class="badge text-bg-secondary ms-1" v-if="file.needs.length > 0">{{
            file.needs.length
          }} dependencies</span>
      </template>
      <template #buttons>
        <button class="btn btn-primary btn-circle" @click="renameFile($event, name)"><i class="fa fa-edit"></i></button>
        <button class="btn btn-danger btn-circle" @click="deleteFile($event, name)"><i class="fa fa-trash"></i></button>
      </template>
      <template #body>
        <div class="release-file-settings">
          <h6>Target settings</h6>
          <p class="text-body-secondary">Define the location of the target file in the repository and define the IRI of
            the resulting ontology.</p>
          <div class="input-group input-group-sm mb-3">
            <span class="input-group-text">Path</span>
            <input v-model="file.target.file" type="text" class="form-control">
          </div>

          <div class="input-group input-group-sm mb-3">
            <span class="input-group-text">IRI</span>
            <input v-model="file.target.iri" type="text" class="form-control">
          </div>

          <div class="input-group input-group-sm mb-3">
            <span class="input-group-text">Annotations</span>
            <textarea :value="Object.entries(file.target.ontology_annotations).map(([k,v]) => `${k}: ${v}`).join('\n')"
                      @change="setAnnotations(name, $event.target?.value)"
                      class="form-control">
            </textarea>
          </div>


          <h6>Source settings</h6>
          <p class="text-body-secondary">
            Add files that contain terms, individuals, and relations which should be
            included in the OWL ontology. Alternatively, add previously built owl files which should be merged to built
            the target ontology.
          </p>
          <template v-for="source in file.sources">
            <div class="input-group input-group-sm mb-3">
              <span class="input-group-text">Source</span>
              <input v-model="source.file" type="text" class="form-control">

              <span class="input-group-text">Type</span>
              <select v-model="source.type" class="form-select" style="flex: unset; width: auto">
                <option value="classes">Classes</option>
                <option value="relations">Relations</option>
                <option value="individuals">Individuals</option>
                <option value="owl">OWL</option>
              </select>
              <button class="btn btn-danger" @click="file.sources = file.sources.filter(x => x != source)">
                <i class="fa fa-trash"></i>
              </button>
            </div>
          </template>
          <button class="mb-3 btn btn-sm btn-primary add-dependency"
                  @click="file.sources.push({file: '', type: 'classes'})">
            <i class="fa fa-add"></i>
            Add source
          </button>


          <h6>Dependency settings</h6>
          <p class="text-body-secondary">
            Specify which other files have to be loaded when building this file.
          </p>

          <template v-for="need in file.needs">

            <div class="input-group input-group-sm mb-3">
              <span class="input-group-text">Dependency</span>
              <input disabled :value="releaseScript.files[need]?.target.file ?? need"
                     type="text" class="form-control">
              <button @click="deleteDependency(name, need)" class="btn btn-danger">
                <i class="fa fa-trash"></i>
              </button>
            </div>
          </template>
          <button class="mb-3 btn btn-sm btn-primary add-dependency" @click="addDependency(name)">
            <i class="fa fa-add"></i>
            Add dependency
          </button>
        </div>
      </template>
    </CollapsibleCard>
    <button class="mb-3 btn btn-sm btn-primary add-file" @click="addFile">
      <i class="fa fa-add"></i>
      Add file
    </button>
  </div>

</template>

<style scoped lang="scss">

.release-file-settings {
  display: grid;
  grid-template-columns: 1fr auto;
  grid-gap: 0 16px;

  & > h6, & > p {
    grid-column: 1/3
  }

  & > .input-group {
    grid-column: 1;
  }

  & > label {
    grid-column: 1;
  }

  & > .btn {
    width: fit-content;
    justify-self: start;
    grid-column: 1;
  }
}

.files {
  display: flex;
  flex-direction: column;
  gap: 14px
}

.btn.add-file {
  width: fit-content;
}

</style>

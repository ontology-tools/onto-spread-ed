<script lang="ts" setup>
import {BuildConfiguration, Project} from "@ontospreaded/js-core";
import CollapsibleCard from "../common/CollapsibleCard.vue";

const props = defineProps<{
  project: Project
  buildConfiguration: BuildConfiguration
}>()

function setAnnotations(name: string, annotations: string) {
  props.project.files[name].target.ontology_annotations =
      Object.fromEntries(annotations.split("\n").map(l => l.split(": ")))
}

function setArgs(step: number, args: string) {
  props.buildConfiguration.stages[step].args = Object.fromEntries(args
      .split("\n")
      .map(l => l.split(": "))
      .map(([k, v]) => {
        if (v === "true") {
          return [k, true]
        } else if (v === "false") {
          return [k, false]
        } else if (!isNaN(Number(v))) {
          return [k, Number(v)]
        } else {
          return [k, v]
        }
      }))
}

function addDependency(name: string) {
  bootbox.prompt({
    title: `Add dependency for ${name}`,
    inputType: "select",
    inputOptions: Object.entries(props.project.files)
        .filter(([k, _]) => k != name)
        .map(([k, v]) => ({
          text: v.target.file,
          value: k
        })),
    callback(value: string) {
      if (value) {
        props.project.files[name].needs.push(value)
      }
    }
  })
}

function deleteDependency(name: string, dependency: string) {
  props.project.files[name].needs = props.project.files[name].needs.filter(x => x != dependency)
}

function addFile() {
  bootbox.prompt({
    title: `What is the name of the file?`,
    inputType: "text",
    callback(value: string) {
      if (value) {
        value = value.trim().replace(/[ ,./\-!?=]/, "_")
        props.project.files[value] = {
          target: {
            file: "",
            iri: "",
            ontology_annotations: {},
            publish: true
          },
          sources: [],
          needs: [],
          addParentsFile: null,
          renameTermFile: null
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
        props.project.files[value] = props.project.files[name]
        delete props.project.files[name]
      }
    }
  })
}

function addStep(event: MouseEvent, before: number) {
  event.preventDefault()

  props.buildConfiguration.stages.splice(before, 0, {args: {}, name: "NEW_STEP"})
}

function deleteStep(event: MouseEvent, index: number) {
  event.preventDefault()

  const step = props.buildConfiguration.stages[index]

  bootbox.confirm({
    title: `Delete step '${step.name}'`,
    message: `Do you want to remove the build stage '${step.name}'?`,
    buttons: {
      confirm: {
        label: `Delete ${step.name}`,
        className: "btn-danger",
      },
      cancel: {
        label: "Keep it",
        className: "btn-success"
      }
    },
    callback(result: boolean) {
      if (result) {
        props.buildConfiguration.stages.splice(index, 1)
      }
    }
  })
}

function deleteFile(event: MouseEvent, name: string) {

  event.preventDefault();
  bootbox.confirm({
    title: `Delete '${name}'`,
    message: `Do you want to delete the file '${name}'? It will remove the file ${props.project.files[name].target.file} from the project.`,
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
        delete props.project.files[name]
      }
    }
  })
}

</script>

<template>

  <div class="files">
    <h3>Files</h3>
    <CollapsibleCard v-for="(file, name) in project.files">
      <template #title>
        {{ name }} - {{ file.target.file }}
        <span class="badge text-bg-secondary">{{ file.sources.length }} sources</span>
        <span v-if="file.needs.length > 0" class="badge text-bg-secondary ms-1">{{
            file.needs.length
          }} dependencies</span>
      </template>
      <template #buttons>
        <button class="btn btn-primary btn-sm btn-circle" @click="renameFile($event, name)"><i class="fa fa-edit"></i>
        </button>
        <button class="btn btn-danger btn-sm btn-circle" @click="deleteFile($event, name)"><i class="fa fa-trash"></i>
        </button>
      </template>
      <template #body>
        <div class="release-file-settings">
          <h6>Target settings</h6>
          <p class="text-body-secondary">Define the location of the target file in the repository and define the IRI of
            the resulting ontology.</p>
          <div class="form-check form-switch mb-3">
            <input v-model="file.target.publish" class="form-check-input" role="switch" type="checkbox">
            <span class="form-check-label">Publish the file to GitHub</span>
          </div>
          <div class="input-group input-group-sm mb-3">
            <span class="input-group-text">Path</span>
            <input v-model="file.target.file" class="form-control" type="text">
          </div>

          <div class="input-group input-group-sm mb-3">
            <span class="input-group-text">IRI</span>
            <input v-model="file.target.iri" class="form-control" type="text">
          </div>

          <div class="input-group input-group-sm mb-3">
            <span class="input-group-text">Annotations</span>
            <textarea :value="Object.entries(file.target.ontology_annotations).map(([k,v]) => `${k}: ${v}`).join('\n')"
                      class="form-control"
                      @change="setAnnotations(name, ($event.target as HTMLTextAreaElement).value)">
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
              <input v-model="source.file" class="form-control" type="text">

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
                  @click="file.sources.push({file: '', type: 'classes', spreadsheet_schema: 'default'})">
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
              <input :value="project.files[need]?.target.file ?? need" class="form-control"
                     disabled type="text">
              <button class="btn btn-danger" @click="deleteDependency(name, need)">
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
    <div class="d-flex gap-2">
      <button class="mb-3 btn btn-sm btn-primary add-file" @click="addFile">
        <i class="fa fa-add"></i>
        Add file
      </button>
    </div>
  </div>


  <h3>Stages of {{ buildConfiguration.name }}</h3>
  <button class="btn btn-outline-primary add-step mb-3" @click="addStep($event, 0)">
    <i class="fa fa-plus-square"></i> Add step here
  </button>
  <template v-for="(step, index) in buildConfiguration.stages">
    <div class="header">
      <h6> {{ step.name }}</h6>
      <span></span>
      <button class="btn btn-danger btn-sm btn-circle" style="margin-bottom: .5rem" @click="deleteStep($event, index)">
        <i class="fa fa-trash"></i>
      </button>
    </div>
    <div class="input-group input-group-sm mb-1">
      <span class="input-group-text">Build stage</span>
      <input v-model="step.name" class="form-control" type="text">
    </div>

    <div class="input-group input-group-sm mb-3">
      <span class="input-group-text">Arguments</span>
      <textarea :value="Object.entries(step.args).map(([k,v]) => `${k}: ${v}`).join('\n')"
                class="form-control"
                @change="setArgs(index, ($event.target as HTMLTextAreaElement).value)">
            </textarea>
    </div>
    <button class="btn btn-outline-primary add-step mb-3" @click="addStep($event, index + 1)">
      <i class="fa fa-plus-square"></i> Add step here
    </button>
  </template>


  <div class="d-flex gap-2">
    <slot name="buttons"></slot>
  </div>


</template>

<style lang="scss" scoped>

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

.header {
  display: flex;
  gap: 14px;

  .title {
    font-size: large;
  }

  span {
    flex-grow: 1;
  }

  i {
    align-self: center;
    transition: transform 1s;
  }
}

.btn.add-step {
  width: 100%;
  border-style: dashed;
}

</style>

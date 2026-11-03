<script lang="ts" setup>
import {computed} from "vue";
import {useRoute, useRouter} from "vue-router";
import {BuildConfiguration, Project} from "@ontospreaded/js-core";
import {alertDialog, confirmDialog, promptDialog} from "../../common/bootbox";
import KeyValueEditor from "./KeyValueEditor.vue";

const props = defineProps<{ project: Project, availableStages: string[] }>()

const route = useRoute();
const router = useRouter();

const configurations = computed(() => props.project.build_configurations);

const selectedIndex = computed(() => {
  const i = Number(route.query.config ?? 0);
  return Number.isInteger(i) && i >= 0 && i < configurations.value.length ? i : 0;
});
const configuration = computed<BuildConfiguration | undefined>(() => configurations.value[selectedIndex.value]);

function select(index: number) {
  router.replace({query: {...route.query, config: String(index)}});
}

async function askName(title: string, value = ""): Promise<string | null> {
  const name = (await promptDialog({title, inputType: "text", value}))?.trim();
  if (!name) return null;
  if (configurations.value.some(c => c.name === name)) {
    await alertDialog({title, message: `There already is a build configuration named '${name}'.`});
    return null;
  }
  return name;
}

async function addConfiguration() {
  const name = await askName("Name of the new build configuration");
  if (name === null) return;

  configurations.value.push({name, description: null, stages: []});
  select(configurations.value.length - 1);
}

async function duplicateConfiguration(c: BuildConfiguration) {
  const name = await askName(`Name of the copy of '${c.name}'`, `${c.name} (copy)`);
  if (name === null) return;

  configurations.value.push({...JSON.parse(JSON.stringify(c)), name});
  select(configurations.value.length - 1);
}

async function renameConfiguration(c: BuildConfiguration) {
  const name = await askName("New name of the build configuration", c.name);
  if (name !== null) c.name = name;
}

async function deleteConfiguration(index: number) {
  const c = configurations.value[index];
  const confirmed = await confirmDialog({
    title: `Delete '${c.name}'`,
    message: `Do you want to delete the build configuration '${c.name}'?`,
    buttons: {
      confirm: {label: `Delete ${c.name}`, className: "btn-danger"},
      cancel: {label: "Keep it", className: "btn-success"},
    },
  });
  if (!confirmed) return;

  configurations.value.splice(index, 1);
  select(Math.max(0, index - 1));
}

function addStage(c: BuildConfiguration, before: number) {
  c.stages.splice(before, 0, {name: props.availableStages[0] ?? "", args: {}});
}

function moveStage(c: BuildConfiguration, index: number, by: number) {
  const [stage] = c.stages.splice(index, 1);
  c.stages.splice(index + by, 0, stage);
}

async function deleteStage(c: BuildConfiguration, index: number) {
  const stage = c.stages[index];
  const confirmed = await confirmDialog({
    title: `Delete stage '${stage.name}'`,
    message: `Do you want to remove the build stage '${stage.name}'?`,
    buttons: {
      confirm: {label: `Delete ${stage.name}`, className: "btn-danger"},
      cancel: {label: "Keep it", className: "btn-success"},
    },
  });
  if (confirmed) c.stages.splice(index, 1);
}
</script>

<template>
  <ul class="nav nav-pills mb-3">
    <li v-for="(c, i) in configurations" :key="i" class="nav-item">
      <a :class="{active: i === selectedIndex}" class="nav-link" href="#" @click.prevent="select(i)">{{ c.name }}</a>
    </li>
    <li class="nav-item">
      <button class="btn btn-link nav-link" type="button" @click="addConfiguration">
        <i class="fa fa-add"></i> Add configuration
      </button>
    </li>
  </ul>

  <p v-if="!configuration" class="text-body-secondary">
    The project has no build configuration yet. Releases need at least one.
  </p>

  <template v-else>
    <div class="d-flex align-items-center gap-2 mb-3">
      <h5 class="mb-0 flex-grow-1">{{ configuration.name }}</h5>
      <button class="btn btn-sm btn-outline-primary" type="button" @click="renameConfiguration(configuration)">
        <i class="fa fa-edit"></i> Rename
      </button>
      <button class="btn btn-sm btn-outline-primary" type="button" @click="duplicateConfiguration(configuration)">
        <i class="fa fa-copy"></i> Duplicate
      </button>
      <button class="btn btn-sm btn-outline-danger" type="button" @click="deleteConfiguration(selectedIndex)">
        <i class="fa fa-trash"></i> Delete
      </button>
    </div>

    <div class="mb-4">
      <label class="form-label" for="build-description">Description</label>
      <textarea id="build-description" :value="configuration.description ?? ''" class="form-control form-control-sm"
                rows="2" @change="configuration.description = ($event.target as HTMLTextAreaElement).value || null">
      </textarea>
    </div>

    <h6>Stages</h6>
    <p v-if="selectedIndex === 0" class="text-body-secondary">
      The first build configuration is preselected when starting a release.
    </p>
    <ol class="list-group list-group-numbered mb-2">
      <li v-for="(stage, i) in configuration.stages" :key="i" class="list-group-item d-flex gap-2">
        <div class="flex-grow-1">
          <div class="input-group input-group-sm mb-2">
            <span class="input-group-text">Stage</span>
            <select v-model="stage.name" class="form-select">
              <option v-if="!availableStages.includes(stage.name)" :value="stage.name">
                {{ stage.name }} (unknown stage)
              </option>
              <option v-for="s in availableStages" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
          <KeyValueEditor :entries="stage.args" key-label="Argument" typed/>
        </div>
        <div class="btn-group-vertical btn-group-sm align-self-start">
          <button :disabled="i === 0" class="btn btn-outline-secondary" title="Move up" type="button"
                  @click="moveStage(configuration, i, -1)">
            <i class="fa fa-arrow-up"></i>
          </button>
          <button :disabled="i === configuration.stages.length - 1" class="btn btn-outline-secondary"
                  title="Move down" type="button" @click="moveStage(configuration, i, 1)">
            <i class="fa fa-arrow-down"></i>
          </button>
          <button class="btn btn-outline-secondary" title="Insert a stage below" type="button"
                  @click="addStage(configuration, i + 1)">
            <i class="fa fa-plus"></i>
          </button>
          <button class="btn btn-outline-danger" title="Delete" type="button" @click="deleteStage(configuration, i)">
            <i class="fa fa-trash"></i>
          </button>
        </div>
      </li>
    </ol>
    <button class="btn btn-sm btn-outline-primary" type="button"
            @click="addStage(configuration, configuration.stages.length)">
      <i class="fa fa-add"></i> Add stage
    </button>
  </template>
</template>

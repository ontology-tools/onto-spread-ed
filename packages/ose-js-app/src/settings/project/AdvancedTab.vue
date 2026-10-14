<script lang="ts" setup>
import {ref, watch} from "vue";
import {Project} from "@ontospreaded/js-core";

const props = defineProps<{ project: Project }>()
const emit = defineEmits<{ (e: "replace", project: Project): void }>()

const text = ref("");
const error = ref<string | null>(null);

watch(() => props.project, p => {
  text.value = JSON.stringify(p, null, 2);
  error.value = null;
}, {immediate: true, deep: true});

function apply() {
  try {
    const parsed = JSON.parse(text.value);
    if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
      throw new Error("The configuration must be a JSON object.");
    }
    error.value = null;
    emit("replace", parsed);
  } catch (e: any) {
    error.value = e.message;
  }
}
</script>

<template>
  <p class="text-body-secondary">
    The complete project configuration as JSON, including the custom spreadsheet schemas. Applied changes are only
    stored when the project is saved; the server validates them then.
  </p>
  <textarea v-model="text" class="form-control font-monospace mb-2" rows="30" spellcheck="false"></textarea>
  <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>
  <button class="btn btn-sm btn-primary" type="button" @click="apply">
    <i class="fa fa-check"></i> Apply
  </button>
</template>

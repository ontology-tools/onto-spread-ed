<script lang="ts" setup>
import {ref} from "vue";

/**
 * Edits the entries of `entries` in place. With `typed`, values are parsed: `true`/`false` become booleans,
 * numbers become numbers and values starting with `[` or `{` are parsed as JSON.
 */
const props = withDefaults(defineProps<{
  entries: Record<string, any>
  keyLabel?: string
  valueLabel?: string
  typed?: boolean
}>(), {keyLabel: "Key", valueLabel: "Value", typed: false})

function format(value: any): string {
  if (!props.typed || typeof value === "string") return value ?? "";
  return JSON.stringify(value);
}

function parse(value: string): any {
  if (!props.typed) return value;

  const v = value.trim();
  if (v === "true" || v === "false") return v === "true";
  if (v !== "" && !isNaN(Number(v))) return Number(v);
  if (v.startsWith("[") || v.startsWith("{")) {
    try {
      return JSON.parse(v);
    } catch {
      // keep it as a string
    }
  }
  return value;
}

/** Key whose rename was rejected, with the reason */
const renameError = ref<{ key: string, message: string } | null>(null);

/** Renames `oldKey` while keeping the order of the entries */
function rename(oldKey: string, input: HTMLInputElement) {
  const newKey = input.value.trim();
  const error = newKey === "" ? `The ${props.keyLabel.toLowerCase()} must not be empty` :
      newKey !== oldKey && newKey in props.entries ? `'${newKey}' exists already` : null;
  if (error !== null) {
    input.value = oldKey;
    renameError.value = {key: oldKey, message: error};
    return;
  }
  renameError.value = null;
  if (newKey === oldKey) return;

  const entries = Object.entries(props.entries);
  for (const [k] of entries) delete props.entries[k];
  for (const [k, v] of entries) props.entries[k === oldKey ? newKey : k] = v;
}

function add() {
  let key = "new", i = 1;
  while (key in props.entries) key = `new_${i++}`;
  props.entries[key] = "";
}
</script>

<template>
  <div class="key-value-editor">
    <div v-for="(value, key) in entries" :key="key" class="input-group input-group-sm mb-2 has-validation">
      <span class="input-group-text">{{ keyLabel }}</span>
      <input :class="{'is-invalid': renameError?.key === key}" :value="key" class="form-control key" type="text"
             @change="rename(key as string, $event.target as HTMLInputElement)">
      <span class="input-group-text">{{ valueLabel }}</span>
      <input :value="format(value)" class="form-control" type="text"
             @change="entries[key] = parse(($event.target as HTMLInputElement).value)">
      <button class="btn btn-outline-danger" title="Remove" type="button" @click="delete entries[key]">
        <i class="fa fa-trash"></i>
      </button>
      <div v-if="renameError?.key === key" class="invalid-feedback">{{ renameError.message }}</div>
    </div>
    <button class="btn btn-sm btn-outline-primary" type="button" @click="add">
      <i class="fa fa-add"></i> Add {{ keyLabel.toLowerCase() }}
    </button>
  </div>
</template>

<style scoped>
.key {
  flex: 0 1 30%;
}
</style>

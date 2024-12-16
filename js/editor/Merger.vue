<script setup lang="ts">
import {MergeConflict} from "../common/model.ts";
import {computed, onMounted, ref, watch, watchEffect} from "vue";

onMounted(() => {
  document.body.style.removeProperty("overflow")
})

const props = defineProps<{
  conflicts: MergeConflict[],
}>()

const merged_data = defineModel<Record<string, string | number | boolean | null>[]>();

const emits = defineEmits<{
  (e: 'save', strategy: "manual" | "theirs" | "ours"): void,
}>()

const conflicts_by_row = computed(() => {
  const result: Record<number, MergeConflict[]> = {}
  for (const conflict of props.conflicts) {
    if (!result[conflict.row]) {
      result[conflict.row] = []
    }
    result[conflict.row].push(conflict)
  }
  return result
})

const resolved = ref<{ [k: number]: { [k: string]: string | number | boolean | null } }>({})

watchEffect(() => {
  resolved.value = Object
      .entries(conflicts_by_row.value)
      .reduce((acc, [r, v]) => ({...acc, [r]: v.reduce((prev, cur) => ({...prev, [cur.col]: null}), {})}), {})
})

const allResolved = computed(() => Object.values(resolved.value).every(v => Object.values(v).every(v => v !== null)))

watch(resolved, () => {
  for (const row in resolved.value) {
    for (const col in resolved.value[row]) {
      if (resolved.value[row][col] === null) {
        return
      } else {
        merged_data.value[row][col] = resolved.value[row][col]
      }
    }
  }
}, {deep: true})

function save() {
  emits('save', 'manual')
}

function saveTheirs() {
  for (const conflict of props.conflicts) {
    merged_data.value[conflict.row][conflict.col] = conflict.their_value
  }
  emits('save', 'theirs')
}

function saveOurs() {
  for (const conflict of props.conflicts) {
    merged_data.value[conflict.row][conflict.col] = conflict.our_value
  }
  emits('save', 'ours')
}


function highlight(row: number, col: string, selfValue: string): string[] {
  const val = resolved.value?.[row]?.[col];

  if (val === null) {
    return []
  } else if (val === selfValue) {
    return ["text-success"]
  } else {
    return ["text-danger"]
  }
}

</script>

<template>
  <div class="container">

    <div class="callout callout-info">
      <h5>Resolving merge conflicts</h5>
      <p>
        While your worked on the file, other users have also made changes to it. Their and your changes conflict.
        The conflicts are shown below.
      </p>
      <p>
        For each conflict, you can choose to use your value, the value from the previous
        version, the value from the other user, or provide a new value. Click the checkmark symbol next to one of the
        values to accept this version. When you resolved all conflicts, click the "Save and complete merge" button.
      </p>
      <p>
        Alternatively, you can choose to overwrite their changes with yours, or to discard your changes and accept
        theirs.
      </p>
    </div>


    <div class="buttons">
      <button class="btn btn-success" :disabled="!allResolved" @click="save()"><i class="fa fa-save"></i>Save and
        complete merge
      </button>
      <button class="btn btn-danger" @click="saveTheirs()"><i class="fa fa-globe"></i>Loose your changes and use their
        version
      </button>
      <button class="btn btn-danger" @click="saveOurs()"><i class="fa fa-user"></i>Overwrite their change with yours
      </button>
    </div>

    <div v-for="row in Object.keys(conflicts_by_row)" class="card bg-danger-subtle">
      <div class="card-body">
        <h5 class="card-title">{{ merged_data[row]["Label"] }} [{{ merged_data[row]["ID"] }}]</h5>
        <h6 class="card-subtitle mb-3">Row {{ row }}</h6>
        <table class="table">
          <thead>
          <tr>
            <th scope="col">Column</th>
            <th scope="col">Your value</th>
            <th scope="col">Previous value</th>
            <th scope="col">Their value</th>
            <th scope="col">Final value</th>
          </tr>
          </thead>
          <tbody>
          <tr v-for="conflict in conflicts_by_row[row]">
            <th scope="row">{{ conflict.col }}</th>
            <td :class="highlight(row, conflict.col, conflict.our_value)">
              <p>
                <template v-for="line in conflict.our_value.split('\n')">
                  {{ line }}
                  <br>
                </template>
              </p>
              <button title="Use my value" class="btn btn-success"
                      @click="resolved[row][conflict.col] = conflict.our_value">
                <i class="fa fa-check"></i>
              </button>
            </td>
            <td :class="highlight(row, conflict.col, conflict.base_value)">
              <p>
                <template v-for="line in conflict.base_value.split('\n')">
                  {{ line }}
                  <br>
                </template>
              </p>
              <button title="Don't change the value" class="btn btn-success"
                      @click="resolved[row][conflict.col] = conflict.base_value">
                <i class="fa fa-check"></i>
              </button>
            </td>
            <td :class="highlight(row, conflict.col, conflict.their_value)">
              <p>
                <template v-for="line in conflict.their_value.split('\n')">
                  {{ line }}
                  <br>
                </template>
              </p>
              <button title="Use their value" class="btn btn-success"
                      @click="resolved[row][conflict.col] = conflict.their_value">
                <i class="fa fa-check"></i>
              </button>
            </td>
            <td>
              <textarea type="text" v-model="resolved[row][conflict.col]"
                        style="width: 300px"
                        v-if="resolved?.[row]?.[conflict.col] !== undefined">
              </textarea>
            </td>
          </tr>
          </tbody>
        </table>
      </div>
    </div>

  </div>
</template>

<style scoped lang="scss">
.conflict {
  display: flex;
  margin-bottom: 10px;
}

.container > * {
  margin-bottom: 1.25rem;

  td.text-danger {
    text-decoration: line-through;
  }
}

.buttons {
  display: flex;
  gap: 1.25rem;

  button i {
    margin-right: 0.75rem;
  }
}

</style>

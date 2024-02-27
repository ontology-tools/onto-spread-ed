<script setup lang="ts">

import {Diagnostic, Term} from "./model.ts";
import {computed} from "vue";

const props = defineProps<{
  error: Diagnostic,
  term?: Term,
  short_repository_name: string
}>()

const item = computed(() => !!props.term ? props.term : props.error)

const has_id = computed<boolean>(() => !!item.value['id'])
const typ = computed<"id" | "search">(() => has_id ? "id" : "search")
const goto = computed<string>(() => has_id ? item.value["id"] : item.value["label"])

</script>

<template>
  <template v-if="item.hasOwnProperty('origin') && item.origin">
    <a target="_blank"
       :href="`/direct?type=${typ}&repo=${short_repository_name}&sheet=${item.origin[0]}&go_to_row=${goto}`">
      <i>
        at <b>{{ item.origin[0] }}</b>
        <template v-if="'row' in error"> row <b>{{ error['row'] }}</b></template>
        <template v-if="'column' in error"> column <b>{{ error.column }}</b></template>
      </i>
    </a>
  </template>
</template>

<style scoped lang="scss">

</style>

<script setup lang="ts">

import {computed} from "vue";
import {Diagnostic, Term} from "@ose/js-core";

const props = defineProps<{
  short_repository_name: string,
  error?: Diagnostic,
  term: Term
} | {
  short_repository_name: string,
  error: Diagnostic,
  term?: Term
}>()
declare var URLS: { [key: string]: any }
const item = computed(() => (!!props.term ? props.term : props.error)!)
const prefix_url = URLS.prefix
</script>

<template>
  <template v-if="item.hasOwnProperty('origin') && item.origin">
    <a target="_blank"
       :href="`${prefix_url}/edit/${short_repository_name}/${item.origin[0]}?row=${item.origin[1]}`">
      <slot>
        <i>
          at <b>{{ item.origin[0] }}</b>
          <template v-if="error && 'row' in error"> row <b>{{ error['row'] }}</b></template>
          <template v-if="error && 'column' in error"> column <b>{{ error.column }}</b></template>
          <template v-if="!error && item.origin[1] >= 0"> row <b>{{ item.origin[1] }}</b></template>
        </i>
      </slot>
    </a>
  </template>
</template>

<style scoped lang="scss">

</style>

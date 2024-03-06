<script setup lang="ts">

import {Diagnostic, Term} from "./model.ts";
import {computed} from "vue";

const props = defineProps<{
  error?: Diagnostic,
  term?: Term,
  short_repository_name: string
}>()

const item = computed(() => !!props.term ? props.term : props.error)
</script>

<template>
  <template v-if="item.hasOwnProperty('origin') && item.origin">
    <a target="_blank"
       :href="`/edit/${short_repository_name}/${item.origin[0]}?row=${item.origin[1]}`">
      <slot>
        <i>
          at <b>{{ item.origin[0] }}</b>
          <template v-if="'row' in error"> row <b>{{ error['row'] }}</b></template>
          <template v-if="'column' in error"> column <b>{{ error.column }}</b></template>
        </i>
      </slot>
    </a>
  </template>
</template>

<style scoped lang="scss">

</style>

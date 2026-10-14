<script setup lang="ts">

import {computed} from "vue";
import {useRouter} from "vue-router";
import {Diagnostic, Term} from "@ontospreaded/js-core";

const props = defineProps<{
  short_repository_name: string,
  error?: Diagnostic,
  term: Term
} | {
  short_repository_name: string,
  error: Diagnostic,
  term?: Term
}>()
const router = useRouter()
const editHref = (origin: [string, number]) =>
  router.resolve({name: "edit", params: {repo: props.short_repository_name, path: origin[0].split("/")}, query: {row: origin[1]}}).href
const item = computed(() => (!!props.term ? props.term : props.error)!)
</script>

<template>
  <template v-if="item.hasOwnProperty('origin') && item.origin">
    <a target="_blank"
       :href="editHref(item.origin)">
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

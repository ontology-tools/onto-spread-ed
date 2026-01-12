<script setup lang="ts">

import {Diagnostic, Severity} from "@ose/js-core";
import {computed} from "vue";
import {DIAGNOSTIC_DATA} from "@ose/js-core";

const props = withDefaults(defineProps<{
  diagnostic: Diagnostic,
  severity?: Severity | null,
  format?: "long" | "inline" | "text"
}>(), {
  severity: null,
  format: "long"
});

const badgeClasses = computed(() => ({
  "text-bg-danger": (props.severity ?? data.value.severity) === "error",
  "text-bg-warning": (props.severity ?? data.value.severity) === "warning",
  "text-bg-info": (props.severity ?? data.value.severity) === "info",
}))

const data = computed(() => ({
  severity: DIAGNOSTIC_DATA[props.diagnostic.type].severity,
  title: DIAGNOSTIC_DATA[props.diagnostic.type].title(props.diagnostic),
  message: DIAGNOSTIC_DATA[props.diagnostic.type].message(props.diagnostic),
}))



</script>

<template>
  <template v-if="format === 'long'">
    <h5 v-html="data.title">
    </h5>
    <p v-html="data.message">
    </p>
    <p v-if="$slots.default">
      <slot></slot>
    </p>
  </template>
  <template v-else-if="format === 'inline'">
    <p>
      <span v-html="data.message"></span>
    </p>
  </template>
  <template v-else-if="format === 'text'">
    {{ data.message.replace(/(<([^>]+)>)/ig, "")}}
  </template>

</template>

<style scoped lang="scss">

</style>
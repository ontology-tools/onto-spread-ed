<script setup lang="ts">

import {Diagnostic, Severity} from "./model.ts";
import {computed} from "vue";
import {DIAGNOSTIC_DATA} from "./diagnostic-data.ts";

const props = withDefaults(defineProps<{
  diagnostic: Diagnostic,
  severity?: Severity | null,
  format: "long" | "inline" | "text"
}>(), {
  severity: null
});

const badgeClasses = computed(() => ({
  "text-bg-danger": (props.severity ?? props.diagnostic) === "error",
  "text-bg-warning": (props.severity ?? props.diagnostic) === "warning",
  "text-bg-info": (props.severity ?? props.diagnostic) === "info",
}))

const data = computed(() => ({
  severity: DIAGNOSTIC_DATA[props.diagnostic.type].severity,
  title: DIAGNOSTIC_DATA[props.diagnostic.type].title(props.diagnostic),
  message: DIAGNOSTIC_DATA[props.diagnostic.type].message(props.diagnostic),
}))



</script>

<template>
  <template v-if="format === 'long'">
    <h5>
      {{ data.title }}
    </h5>
    <p>
      {{ data.message}} <br v-if="$slots.default">
      <slot></slot>
    </p>
  </template>
  <template v-else-if="format === 'inline'">
    <span class="badge" :class="badgeClasses" style="text-transform: capitalize">{{ severity ?? data.severity }}</span>
    <template v-html="data.message"></template>
  </template>
  <template v-else-if="format === 'text'">
    {{ data.message.replace(/(<([^>]+)>)/ig, "")}}
  </template>

</template>

<style scoped lang="scss">

</style>
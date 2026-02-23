<script setup lang="ts">
import {Release} from "@ontospreaded/js-core";

const props = defineProps<{
  release: Release,
  details: {
    [key: string]: any,
    errors: {
      [key: string]: any,
    }[]
  }
}>()

</script>

<template>
    <div class="alert alert-danger">
      <h4>An error occurred while building the file</h4>
      <p>
        A technical error occurred. Please contact an administrator.
      </p>
    </div>
    <div class="alert alert-danger" v-for="error in details.errors">
      <template v-if="'code' in error">
        <h6>Command</h6>
        <pre>{{ error.command }}</pre>
        <h6>Return code</h6>
        <p>{{ error.code }}</p>
        <h6>Standard out</h6>
        <pre>{{ error.out }}</pre>
        <h6>Standard error</h6>
        <pre>{{ error.err }}</pre>
      </template>
      <template v-else-if="error.type === 'http-error'">
        <h6 v-if="error.term">Term: {{ error.term }}</h6>
        <p class="mb-1"><strong>HTTP {{ error.status_code }}:</strong> {{ error.response?.['hydra:title'] ?? 'Request failed' }}</p>
        <p v-if="error.response?.['hydra:description']" class="mb-1">{{ error.response['hydra:description'] }}</p>
        <ul v-if="error.response?.violations?.length" class="mb-0">
          <li v-for="v in error.response.violations">
            <strong>{{ v.propertyPath }}</strong>: {{ v.message }}
          </li>
        </ul>
      </template>
      <template v-else>
        <pre>{{ JSON.stringify(error, undefined, 2) }}</pre>
      </template>
    </div>
</template>

<style scoped lang="scss">

</style>

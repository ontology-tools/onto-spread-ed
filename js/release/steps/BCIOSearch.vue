<script setup lang="ts">

import ProgressIndicator from "../ProgressIndicator.vue";

defineProps<{
  data: any,
  release: Release
}>()


defineEmits<{
  (e: 'release-control', type: string, ...args: any[]): void
}>()
</script>

<template>
  <h3>Publishing the release</h3>

  <!--  <TechnicalError v-if="release.state == 'waiting-for-user' && data && (data.errors?.length ?? 0) > 0"-->
  <!--                  :release="release"-->
  <!--                  :details="data"></TechnicalError>-->
  <template v-if="release.state === 'waiting-for-user' && data?.errors?.length > 0">
    <div v-for="error in data.errors" class="alert alert-danger">
      <template v-if="error.details && error?.response?.['hydra:description']">
        <h4>{{ error.response['hydra:title'] }}</h4>
        <p>{{ error.details }}</p>
        <p>{{ error.response['hydra:description'] }}</p>
      </template>
      <pre v-else>{{ JSON.stringify(error, undefined, 2) }}</pre>
    </div>
  </template>

  <ProgressIndicator v-else :details="data" :release="release">
    <p>
      The ontologies are being published to BCIOSearch. This will take a while.<br>
<!--      Hint: The total number of processed entities will increase until around 60%.-->
<!--    <details>-->
<!--      <summary>Click to see why.</summary>-->
<!--      <p>-->
<!--        The process happens in two steps-->
<!--      </p>-->
<!--      <ol>-->
<!--        <li>All new terms are created - but without relations</li>-->
<!--        <li>Relations are added and existing terms get updated</li>-->
<!--      </ol>-->
<!--      This procedure is necessary to ensure that when adding a relation - say, <code>A 'has part' B</code> - for-->
<!--      <code>A</code> the term <code>B</code> exists. In the first step we estimate -->
<!--    </details>-->
    </p>
  </ProgressIndicator>


  <template v-if="release.state === 'completed'">
    <p>
      The ontologies were published to BCIOSearch.
    </p>
  </template>

</template>

<style scoped lang="scss">

</style>

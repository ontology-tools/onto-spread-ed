<script setup lang="ts">
import {computed, ref} from "vue";
import {AutoFixState, Diagnostic as DiagnosticM, Release, Term} from "../../common/model";
import ErrorLink from "../ErrorLink.vue";
import {guessParent} from "../autofix/guessParent"
import ProgressIndicator from "../ProgressIndicator.vue";
import Diagnostic from "../../common/Diagnostic.vue";

declare var URLS: { [key: string]: any }
const prefix_url = URLS.prefix

const props = defineProps<{
  data: {
    [K: string]: {
      errors: DiagnosticM[],
      warnings: DiagnosticM[],
      info: DiagnosticM[]
    }
  } | null,
  release: Release,
  selectedSubStep: string | null
}>()

defineEmits<{
  (e: 'release-control', type: string, ...args: any[]): void
}>()

const autoFixStates = ref<{ [k: string]: AutoFixState }>({})

function autoFixState(diag: DiagnosticM): AutoFixState | null {
  const id = JSON.stringify(diag)
  return autoFixStates.value[id] ?? null
}

const errors = computed<DiagnosticM[] | null>(() => {
  if (!props.data) {
    return null
  }

  return Object.values(props.data).flatMap((v) => v.errors)
})
const warnings = computed<any[] | null>(() => {
  if (!props.data) {
    return null
  }

  return Object.values(props.data).flatMap((v) => v.warnings)
})

const shortRepoName = computed(() => props.release.release_script.short_repository_name)

async function updateTerm(path: string, id: Term, term: Term): Promise<AutoFixState> {
  const repo = props.release.release_script.short_repository_name

  try {
    const response = await fetch(`${prefix_url}/api/edit/${repo}/${path}`, {
      method: "PATCH",
      body: JSON.stringify({
        id: id,
        term: {
          id: term.id,
          parent: term.sub_class_of[0]?.label,
          label: term.label
        }
      }),
      headers: {"Content-Type": "application/json"}
    })

    if (response.ok) {
      return "fixed"
    } else {
      return "impossible"
    }
  } catch {
    return "impossible"
  }
}

async function autofixUpdateTerm(error: DiagnosticM, id: string, term: Term, path?: string) {
  const wid = JSON.stringify(error)
  if (wid in autoFixStates.value && autoFixStates.value[wid] !== "loaded") {
    return
  }

  autoFixStates.value[wid] = await updateTerm(path ?? error?.term?.origin?.[0] ?? term?.origin?.[0], id, term)
}

async function autofix(error: DiagnosticM) {
  let id = JSON.stringify(error)
  if (id in autoFixStates.value && autoFixStates.value[id] !== "loaded") {
    return
  }

  const repo = props.release.release_script.short_repository_name;
  autoFixStates.value[id] = "loading"
  if (error.type === "unknown-parent") {
    autoFixStates.value[id] = await guessParent(error, repo)
  } else if (error.type === "missing-import") {
    try {
      const response = await fetch(`${prefix_url}/api/external/${repo}/import`, {
        method: "post",
        body: JSON.stringify({
          terms: [{id: error.term.id, label: error.term.label}],
          ontologyId: error.term.id.split(":")[0]
        }),
        headers: {"Content-Type": "application/json"}
      })

      if (response.ok) {
        autoFixStates.value[id] = "fixed"
      }
    } catch (e) {
      autoFixStates.value[id] = "impossible"
      console.error(e)
    }
  } else {
    autoFixStates.value[id] = "impossible"
  }

  if (autoFixStates.value[id] == "loading") {
    autoFixStates.value[id] = "loaded"
  }
}

</script>

<template>
  <h3>Validation</h3>

  <template v-if="!data || Object.keys(data).length === 1 && '__progress' in data">
    <ProgressIndicator :release="release" :details="data || {}">
      All excel files are now being validated. The results will be presented here soon.
    </ProgressIndicator>
  </template>
  <template v-else>
    <div class="alert alert-success" v-if="errors?.length == 0 && warnings?.length == 0">
      <h5>Everything ok</h5>
      Good work! All files are valid. The release process will continue.
    </div>
    <p v-else>
      <span class="text-danger bg-danger-subtle rounded ps-1 pe-1">{{
          errors?.length ?? 0
        }} {{ $filters.pluralise("error", errors) }}</span> and
      <span class="text-warning bg-warning-subtle rounded ps-1 pe-1">{{
          warnings?.length ?? 0
        }} {{ $filters.pluralise("warning", warnings) }}</span>
      were found during the validation. Please fix the errors and save the spreadsheets. Errors are problems which
      prevent
      the release from continuing. Warnings hint at possible problems, but the release might continue without solving
      them.
      When you fixed all errors, restart the release. If you just want to rerun the
      validation, restart the release as well.
    </p>

    <template v-for="source in data ? Object.keys(data) : []">
      <template v-if="selectedSubStep === null || selectedSubStep === source">
        <div v-for="error in data?.[source].errors"
             :class="[`val-error-type-${error.type}`, `val-error-source-${source}`]"
             class="alert alert-danger val val-error"
             role="alert">

          <template v-if="error.type === 'unknown-parent'">
            <Diagnostic :diagnostic="error">
              <ErrorLink :error="error" :short_repository_name="shortRepoName"
                         :term="error.term ?? error.relation"></ErrorLink>
            </Diagnostic>

            <button v-if="release.release_script.short_repository_name.toLowerCase() !== 'addicto'"
                    :class="{'btn-success': autoFixState(error) === 'fixed', 'btn-danger': autoFixState(error) === 'impossible'}"
                    class="btn btn-primary"
                    @click="autofix(error)">
              <i v-if="autoFixState(error) === 'loading'" class="fa fa-spin fa-spinner"></i>
              <i v-if="autoFixState(error) === 'fixed'" class="fa fa-check"></i>
              <i v-if="autoFixState(error) === 'impossible'" class="fa fa-close"></i>
              Try auto fix
            </button>


          </template>
          <template v-else-if="error.type === 'missing-parent'">
            <Diagnostic :diagnostic="error">
              <ErrorLink :error="error" :short_repository_name="shortRepoName"
                         :term="error.term ?? error.relation"></ErrorLink>
            </Diagnostic>
          </template>
          <template v-else-if="error.type === 'no-parent'">
            <Diagnostic :diagnostic="error">
              <ErrorLink :error="error" :short_repository_name="shortRepoName"
                         :term="error.term ?? error.relation"></ErrorLink>
            </Diagnostic>
          </template>
          <template v-else-if="error.type === 'ignored-parent'">
            <Diagnostic :diagnostic="error">
              <ErrorLink :error="error" :short_repository_name="shortRepoName"
                         :term="error.term ?? error.relation"></ErrorLink>
            </Diagnostic>
          </template>
          <template v-else-if="error.type === 'missing-label'">

            <Diagnostic :diagnostic="error">
              <ErrorLink :error="error" :short_repository_name="shortRepoName"
                         :term="error.term ?? error.relation"></ErrorLink>
            </Diagnostic>
          </template>
          <template v-else-if="error.type === 'missing-id'">

            <Diagnostic :diagnostic="error">
              <ErrorLink :error="error" :short_repository_name="shortRepoName"
                         :term="error.term ?? error.relation"></ErrorLink>
            </Diagnostic>
          </template>
          <template v-else-if="error.type === 'unknown-disjoint'">

            <Diagnostic :diagnostic="error">
              <ErrorLink :error="error" :short_repository_name="shortRepoName"
                         :term="error.term ?? error.relation"></ErrorLink>
            </Diagnostic>
          </template>
          <template v-else-if="error.type === 'unknown-relation-value'">

            <Diagnostic :diagnostic="error">
              <ErrorLink :error="error" :short_repository_name="shortRepoName"
                         :term="error.term ?? error.relation"></ErrorLink>
            </Diagnostic>
          </template>
          <template v-else-if="error.type === 'ignored-relation-value'">

            <Diagnostic :diagnostic="error">
              <ErrorLink :error="error" :short_repository_name="shortRepoName"
                         :term="error.term ?? error.relation"></ErrorLink>
            </Diagnostic>
          </template>
          <template v-else-if="error.type === 'unknown-range'">
            <Diagnostic :diagnostic="error">
              <ErrorLink :error="error" :short_repository_name="shortRepoName"
                         :term="error.relation"></ErrorLink>
            </Diagnostic>
          </template>
          <template v-else-if="error.type === 'unknown-domain'">
            <Diagnostic :diagnostic="error">
              <ErrorLink :error="error" :short_repository_name="shortRepoName"
                         :term="error.relation"></ErrorLink>
            </Diagnostic>
          </template>
          <template v-else-if="error.type === 'unknown-relation'">

            <Diagnostic :diagnostic="error">
              <ErrorLink :error="error" :short_repository_name="shortRepoName"
                         :term="error.relation"></ErrorLink>
            </Diagnostic>
          </template>
          <template v-else-if="error.type === 'duplicate'">
            <h5>Conflicting entries (duplicates)</h5>
            <p>
              There are multiple terms for the {{ error.duplicate_field }} <code>{{ error.duplicate_value }}</code>:
            </p>
            <ul>
              <li v-for="mismatch in error.mismatches">
                <p>
                  <span style="text-transform: capitalize">{{ mismatch.field }}</span> is
                  <code v-if="['definition', 'curation status'].indexOf(mismatch.field) >= 0">
                    {{
                      mismatch.a.relations.find(x => x[0]?.label?.endsWith(mismatch.field))?.[1]
                    }}
                  </code>
                  <code v-else>{{ mismatch.a[mismatch.field] }}</code>
                  <br>
                  <ErrorLink :short_repository_name="shortRepoName" :term="mismatch.a"></ErrorLink>
                  <br>
                  and
                  <code v-if="['definition', 'curation status'].indexOf(mismatch.field) >= 0">
                    {{
                      mismatch.b.relations.find(x => x[0]?.label?.endsWith(mismatch.field))?.[1]
                    }}
                  </code>
                  <code v-else>{{ mismatch.b[mismatch.field] }}</code>
                  <br>
                  <ErrorLink :short_repository_name="shortRepoName" :term="mismatch.b"></ErrorLink>
                </p>
              </li>
            </ul>
          </template>
          <template v-else>
            <h5>{{ error.type.replace("-", " ") }}</h5>
            <p>
              {{ error.msg }}<br>

              <ErrorLink :error="error" :short_repository_name="shortRepoName"></ErrorLink>
            </p>
            <pre>{{ JSON.stringify(error, undefined, 2) }}</pre>
          </template>
        </div>


        <div v-for="warning in data?.[source].warnings"
             class="alert alert-warning val val-warning val-warning-type-{{ warning.type }} val-warning-source-{{ source }}"
             role="alert">
          <template v-if="warning.type == 'incomplete-term'">
            <Diagnostic :diagnostic="warning">
              <ErrorLink :error="warning" :short_repository_name="shortRepoName"></ErrorLink>
            </Diagnostic>
          </template>
          <template v-else-if="warning.type === 'unknown-column'">
            <Diagnostic :diagnostic="warning" />
          </template>
          <template v-else-if="warning.type === 'missing-import'">
            <Diagnostic :diagnostic="warning">
              <ErrorLink :error="warning" :short_repository_name="shortRepoName" :term="warning.term"></ErrorLink>
            </Diagnostic>

            <button
                :class="{'btn-success': autoFixState(warning) === 'fixed', 'btn-danger': autoFixState(warning) === 'impossible'}"
                class="btn btn-primary"
                @click="autofix(warning)">
              <i v-if="autoFixState(warning) === 'loading'" class="fa fa-spin fa-spinner"></i>
              <i v-if="autoFixState(warning) === 'fixed'" class="fa fa-check"></i>
              <i v-if="autoFixState(warning) === 'impossible'" class="fa fa-close"></i>
              Import
            </button>
          </template>
          <template v-else-if="warning.type === 'inconsistent-import'">

            <Diagnostic :diagnostic="warning">
              <ErrorLink :error="warning" :short_repository_name="shortRepoName" :term="warning.term"></ErrorLink>
            </Diagnostic>

            <button
                :class="{'btn-success': autoFixState(warning) === 'fixed', 'btn-danger': autoFixState(warning) === 'impossible'}"
                class="btn btn-primary"
                @click="autofixUpdateTerm(warning, warning.term.id, {
                  ...warning.term.id,
                  label: warning.term.label,
                  id: warning.term.id
                })">
              <i v-if="autoFixState(warning) === 'loading'" class="fa fa-spin fa-spinner"></i>
              <i v-if="autoFixState(warning) === 'fixed'" class="fa fa-check"></i>
              <i v-if="autoFixState(warning) === 'impossible'" class="fa fa-close"></i>
              Change
              <template v-if="warning.term.id !== warning.imported_term.id">
                ID to
                <code>{{ warning.imported_term.id }}</code>
              </template>
              <template v-else>label to <code>{{ warning.imported_term.label }}</code></template>
            </button>
          </template>
          <template v-else>
            <h5>{{ warning.type.replace("-", " ") }}</h5>
            <p>
              {{ warning.msg }}<br>

              <ErrorLink :error="warning" :short_repository_name="shortRepoName"></ErrorLink>
            </p>
            <pre>{{ JSON.stringify(warning, undefined, 2) }}</pre>
          </template>
        </div>
      </template>
    </template>
  </template>
</template>

<style scoped lang="scss">

</style>

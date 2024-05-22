<script setup lang="ts">
import {computed, ref} from "vue";
import {AutoFixState, Diagnostic, Release} from "../model.ts";
import ErrorLink from "../ErrorLink.vue";
import {guessParent} from "../autofix/guessParent.ts"
import ProgressIndicator from "../ProgressIndicator.vue";

declare var URLS: { [key: string]: any }
const prefix_url = URLS.prefix

const props = defineProps<{
  data: {
    [K: string]: {
      errors: Diagnostic[],
      warnings: Diagnostic[],
      info: Diagnostic[]
    }
  } | null,
  release: Release
}>()

defineEmits<{
  (e: 'release-control', type: string, ...args: any[]): void
}>()

const autoFixStates = ref<{ [k: string]: AutoFixState }>({})

function autoFixState(diag: Diagnostic): AutoFixState | null {
  const id = JSON.stringify(diag)
  return autoFixStates.value[id] ?? null
}

const errors = computed<Diagnostic[] | null>(() => {
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


async function autofix(error: Diagnostic) {
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
      <div v-for="error in data?.[source].errors"
           class="alert alert-danger val val-error"
           :class="[`val-error-type-${error.type}`, `val-error-source-${source}`]"
           role="alert">

        <template v-if="error.type === 'invalid-value'">
          <h5>Invalid value</h5>
          <p>
            {{ error.msg }}<br>
            <ErrorLink :short_repository_name="shortRepoName" :error="error"></ErrorLink>
          </p>
        </template>
        <template v-else-if="error.type === 'unknown-parent'">
          <h5>Unknown parent</h5>
          <p>
            The parent <code>{{ error.parent.label }}</code> of <code>{{ (error.term ?? error.relation).label }}</code>
            (<code>{{ (error.term ?? error.relation).id || 'no id' }}</code>) is not known.
            <br>

            <ErrorLink :short_repository_name="shortRepoName" :error="error"
                       :term="error.term ?? error.relation"></ErrorLink>
          </p>

          <button class="btn btn-primary"
                  v-if="release.release_script.short_repository_name.toLowerCase() !== 'addicto'"
                  :class="{'btn-success': autoFixState(error) === 'fixed', 'btn-danger': autoFixState(error) === 'impossible'}"
                  @click="autofix(error)">
            <i class="fa fa-spin fa-spinner" v-if="autoFixState(error) === 'loading'"></i>
            <i class="fa fa-check" v-if="autoFixState(error) === 'fixed'"></i>
            <i class="fa fa-close" v-if="autoFixState(error) === 'impossible'"></i>
            Try auto fix
          </button>


        </template>
        <template v-else-if="error.type === 'missing-parent'">
          <h5>Missing parent</h5>
          <p>
            The parent <code>{{ error.parent.label }}</code> (<code>{{ error.parent.id }}</code>) of
            <code>{{ error.term.label }}</code>
            (<code>{{
              error.term.id || ("no id")
            }}
          </code>) is neither defined in the Excel files or imported.
            If it is an external term, add the missing import the entry with
            <code>{{ error.parent.label }} [{{ error.parent.id }}]</code>.
            <br>
            <ErrorLink :short_repository_name="shortRepoName" :error="error"
                       :term="error.term"></ErrorLink>
          </p>
        </template>
        <template v-else-if="error.type === 'ignored-parent'">
          <h5>{{ error.status }} parent</h5>
          <p>
            The parent <code>{{ error.parent.label }}</code> of <code>{{ error.term.label }}</code>
            (<code>{{ error.term.id ?? 'no id' }}</code>) is {{ error.status.toLowerCase() }}.<br>
            <ErrorLink :short_repository_name="shortRepoName" :error="error"
                       :term="error.term"></ErrorLink>
          </p>
        </template>
        <template v-else-if="error.type === 'missing-label'">
          <h5>Missing label</h5>
          <p>
            The term <code>{{ error.term.id }}</code> has no label. <br>
            <ErrorLink :short_repository_name="shortRepoName" :error="error"
                       :term="error.term"></ErrorLink>
          </p>
        </template>
        <template v-else-if="error.type === 'missing-id'">
          <h5>Term has no ID</h5>
          <p>
            The term <code>{{ error.term.label }}</code> has no ID but is also not obsolete or pre-proposed. <br>
            <ErrorLink :short_repository_name="shortRepoName" :error="error"
                       :term="error.term"></ErrorLink>
          </p>
        </template>
        <template v-else-if="error.type === 'unknown-disjoint'">
          <h5>Unknown disjoint class</h5>
          <p>
            The class <code>{{ error.term.label }}</code> (<code>{{ error.term.id }}</code>) is
            specified to
            be disjoint with <code>{{ error.disjoint_class.label }}</code> but it is not known.<br>
            <ErrorLink :short_repository_name="shortRepoName" :error="error"
                       :term="error.term"></ErrorLink>
          </p>
        </template>
        <template v-else-if="error.type === 'unknown-equivalent'">
          <h5>Unknown disjoint class</h5>
          <p>
            The class <code>{{ error.term.label }}</code> (<code>{{ error.term.id }}</code>) is
            specified to
            be logically equivalent to <code>{{ error.equivalent_class.label }}</code> but it is not
            known.<br>
            <ErrorLink :short_repository_name="shortRepoName" :error="error"
                       :term="error.term"></ErrorLink>
          </p>
        </template>
        <template v-else-if="error.type === 'unknown-relation-value'">
          <h5>Unknown value for relation <code>{{ error.relation.label }}</code></h5>
          <p>
            Related term <code>{{ error.value.label }}</code> of <code>{{ error.term.label }}</code>
            (<code>{{
              error.term.id || "no id"
            }}
          </code>) is not known. <br>
            <ErrorLink :short_repository_name="shortRepoName" :error="error"
                       :term="error.term"></ErrorLink>
          </p>
        </template>
        <template v-else-if="error.type === 'ignored-relation-value'">

          <h5>{{ error.status }} value for relation <code>{{ error.relation.label }}</code></h5>
          <p>
            Related term <code>{{ error.value.label }}</code> of <code>{{ error.term.label }}</code>
            (<code>{{ error.term.id ?? 'no id' }}</code>) is {{ error.status.toLowerCase() }}.<br>
            <ErrorLink :short_repository_name="shortRepoName" :error="error"
                       :term="error.term"></ErrorLink>
          </p>
        </template>
        <template v-else-if="error.type === 'unknown-range'">
          <h5>Unknown range</h5>
          <p>
            The range <code>{{ error.relation.range.label }}</code> of
            <code>{{ error.relation.label }}</code>
            (<code>{{
              error.relation.id || "no id"
            }}
          </code>) is not known. <br>
            <ErrorLink :short_repository_name="shortRepoName" :error="error"
                       :term="error.relation"></ErrorLink>
          </p>
        </template>
        <template v-else-if="error.type === 'unknown-domain'">
          <h5>Unknown domain</h5>
          <p>
            The domain <code>{{ error.relation.domain.label }}</code> of
            <code>{{ error.relation.label }}</code>
            (<code>{{ error.relation.id || "no id" }} </code>) is not known. <br>
            <ErrorLink :short_repository_name="shortRepoName" :error="error"
                       :term="error.relation"></ErrorLink>
          </p>
        </template>
        <template v-else-if="error.type === 'unknown-relation'">
          <h5>Unknown relation</h5>
          <p>
            The relation

            <template v-if="error.relation.label">
              <code>{{ error.relation.label }}</code>
              <template v-if="error.relation.id">
                (<code>{{ error.relation.id }}</code>)
              </template>
            </template>
            <template v-else-if="error.relation.id">
              <code>{{ error.relation.id }}</code>
            </template>

            is not known.<br>
            <ErrorLink :short_repository_name="shortRepoName" :error="error"
                       :term="error.relation"></ErrorLink>
          </p>
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

            <ErrorLink :short_repository_name="shortRepoName" :error="error"></ErrorLink>
          </p>
          <pre>{{ JSON.stringify(error, undefined, 2) }}</pre>
        </template>
      </div>


      <div v-for="warning in data?.[source].warnings"
           class="alert alert-warning val val-warning val-warning-type-{{ warning.type }} val-warning-source-{{ source }}"
           role="alert">
        <template v-if="warning.type == 'incomplete-term'">
          <h5>Incomplete term</h5>
          <p>
            There is an incomplete term with no an ID, a label, or a parent defined. Is there an empty line in the
            spreadsheet?<br>
            The line was ignored.<br>

            <ErrorLink :short_repository_name="shortRepoName" :error="warning"></ErrorLink>
          </p>
        </template>
        <template v-else-if="warning.type === 'unknown-column'">
          <h5>Unmapped column</h5>
          <p>
            The column <code>{{ warning.column }}</code> of <code>{{ warning.sheet }}</code> is not mapped
            to any OWL property or internal field.
          </p>
        </template>
        <template v-else-if="warning.type === 'missing-import'">
          <h5>Missing import</h5>
          <p>
            The term <code>{{ warning.term.label }}</code> (<code>{{ warning.term.id }}</code>) has the curation status
            "External" but is not included in the externally imported terms.<br>

            <ErrorLink :short_repository_name="shortRepoName" :error="warning" :term="warning.term"></ErrorLink>
          </p>

          <button class="btn btn-primary"
                  :class="{'btn-success': autoFixState(warning) === 'fixed', 'btn-danger': autoFixState(warning) === 'impossible'}"
                  @click="autofix(warning)">
            <i class="fa fa-spin fa-spinner" v-if="autoFixState(warning) === 'loading'"></i>
            <i class="fa fa-check" v-if="autoFixState(warning) === 'fixed'"></i>
            <i class="fa fa-close" v-if="autoFixState(warning) === 'impossible'"></i>
            Import
          </button>
        </template>
        <template v-else>
          <h5>{{ warning.type.replace("-", " ") }}</h5>
          <p>
            {{ warning.msg }}<br>

            <ErrorLink :short_repository_name="shortRepoName" :error="warning"></ErrorLink>
          </p>
          <pre>{{ JSON.stringify(warning, undefined, 2) }}</pre>
        </template>
      </div>
    </template>
  </template>
</template>

<style scoped lang="scss">

</style>

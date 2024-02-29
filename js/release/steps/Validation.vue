<script setup lang="ts">
import {computed} from "vue";
import {Diagnostic, Release} from "../model.ts";
import ErrorLink from "../ErrorLink.vue";
import ProgressIndicator from "../ProgressIndicator.vue";

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
</script>

<template>
  <h3>Validation</h3>

  <template v-if="!data || Object.keys(data).length === 1 && '__progress' in data">
    <ProgressIndicator :release="release" :details="data">
      All excel files are now being validated. The results will be presented here soon.
    </ProgressIndicator>
  </template>
  <template v-else>
    <div class="alert alert-success" v-if="errors?.length == 0 && warnings?.length == 0">
      <h5>Everything ok</h5>
      Good work! All files are valid. The release process will continue.
    </div>
    <p v-else>
      {{ errors?.length ?? 0 }} errors and {{ warnings?.length ?? 0 }} warnings were found during the validation. Please
      fix the
      errors and save the spreadsheets. When you fixed all errors, restart the release. If you just want to rerun the
      validation, restart the release as well.
    </p>


    <template v-for="source in data ? Object.keys(data) : []">
      <div v-for="error in data?.[source].errors"
           class="alert alert-danger val val-error val-error-type-{{ error.type }} val-error-source-{{ source }}"
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
            The parent <code>{{ error.parent.label }}</code> of <code>{{ error.term.label }}</code>
            (<code>{{ error.term.id || 'no id' }}</code>) is not known.
            <template v-if="!!error.term.id && !error.term.id.startsWith(shortRepoName)">
              The term appears external. If you redefine an external entity ensure to import its
              parent and all of its related terms as well.
            </template>
            <template v-else>
              If it is an external term, ensure that it is imported correctly.
            </template>
            <br>

            <ErrorLink :short_repository_name="shortRepoName" :error="error"
                       :term="error.term"></ErrorLink>
          </p>
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
            <template v-if="!!error.term.id && !error.term.id.startsWith(shortRepoName)">
              The term appears external. If you redefine an external entity ensure to import its
              parent and all of its related terms as well. <br>
              If it is an external term, is missing import the entry with
              <code>{{ error.parent.label }} [{{ error.parent.id }}]</code>.
            </template>
            <template v-else>
              If it is an external term, ensure that it is imported correctly.
            </template>
            <br>
            <ErrorLink :short_repository_name="shortRepoName" :error="error"
                       :term="error.term"></ErrorLink>
          </p>
        </template>
        <template v-else-if="error.type === 'obsolete-parent'">
          <h5>Obsolete parent</h5>
          <p>
            The parent <code>{{ error.parent.label }}</code> of <code>{{ error.term.label }}</code>
            (<code>{{ error.term.id ?? 'no id' }}</code>) is obsolete.<br>
            <ErrorLink :short_repository_name="shortRepoName" :error="error"
                       :term="error.term"></ErrorLink>
          </p>
        </template>
        <template v-else-if="error.type === 'missing-label'">
          <h5>Unknown label</h5>
          <p>
            The term <code>{{ error.term.id }}</code> has no label. <br>
            <ErrorLink :short_repository_name="shortRepoName" :error="error"
                       :term="error.term"></ErrorLink>
          </p>
        </template>
        <template v-else-if="error.type === 'unknown-label'">
          <h5>Missing label</h5>
          <p>
            The term <code>{{ error.term.label }}</code> could not be resolved. Ensure it has an ID and
            if it is external ensure it is imported properly. <br>
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
        <template v-else-if="warning.type === 'duplicate-term'">
                    <h5>Duplicate terms</h5>
                    <p>
                        The term <code>{{ warning.duplicates[0].label }}</code>
                        (<code>{{ warning.duplicates[0].id }}</code>) is defined in multiple places:<br>
                    </p>
                    <ul>
                          <li v-for="d in warning.duplicates"><a href="#{{ origin_link(d) }}"><code>{{ d.origin[0] }}</code></a></li>
                    </ul>
          </template>
        <template v-else-if="warning.type === 'unknown-column'">
                    <h5>Unmapped column</h5>
                    <p>
                        The column <code>{{ warning.column }}</code> of <code>{{ warning.sheet }}</code> is not mapped
                        to any OWL property or internal field.
                    </p>
        </template>
        <template v-else>
          <h5>{{ warning.type.replace("-", " ") }}</h5>
          <p>
            {{ warning.msg }}<br>

            <ErrorLink :short_repository_name="shortRepoName" :error="warning"></ErrorLink>
          </p>
        </template>
      </div>
    </template>
  </template>
</template>

<style scoped lang="scss">

</style>

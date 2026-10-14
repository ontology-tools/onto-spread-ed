<script setup lang="ts">
import {ref} from "vue";
import {useRouter} from "vue-router";
import {cachedRepos, fetchRepos, type Repo} from "../api";

const router = useRouter();
const repos = ref<Repo[] | null>(null);
const error = ref<string | null>(null);

function show(r: NonNullable<typeof repos.value>) {
  if (r.length === 1) {
    router.replace(`/repo/${r[0].short}`);
  } else {
    repos.value = r;
  }
}

const known = cachedRepos();
if (known) show(known);
else fetchRepos().then(show).catch(e => {
  error.value = e.message;
});
</script>

<template>
  <div v-if="error" class="alert alert-danger">{{ error }}</div>
  <template v-else-if="repos !== null">
    <template v-if="repos.length === 0">
      <h2>No repositories</h2>
      <p>There are no repositories configured for this instance. Add one in the
        <RouterLink to="/admin/settings">Settings</RouterLink>
        or add it in the configuration.
      </p>
    </template>
    <template v-else>
      <h2>Choose a project repository:</h2>
      <div class="row align-stretch">
        <div v-for="repo in repos" :key="repo.short" class="col-sm-6 col-md-4 col-lg-3 m-2">
          <RouterLink class="card bg-light" :to="`/repo/${repo.short}`"
                      style="height: 100%; text-decoration: none; border-width: 2px 2px 4px 2px">
            <div class="section p-5 text-center fs-2">{{ repo.short }}</div>
            <div class="card-body text-center">{{ repo.full }}</div>
          </RouterLink>
        </div>
      </div>
    </template>
  </template>
  <div v-else class="spinner-border spinner-border-sm mt-3" role="status"></div>
</template>

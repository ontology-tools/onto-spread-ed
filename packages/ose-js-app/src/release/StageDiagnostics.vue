<script lang="ts" setup>
import {computed, reactive} from "vue";
import {DIAGNOSTIC_DATA, type Diagnostic, type StageDetails} from "@ontospreaded/js-core";

// Warnings and infos a stage logged. Errors are left to the step views, which show them when the stage failed.
const props = defineProps<{ details: StageDetails | null }>();

type Severity = "warning" | "info";
type Group = { key: string, severity: Severity, title: string, items: Diagnostic[] };

const PAGE = 50;
const SEVERITIES: { severity: Severity, field: "warnings" | "infos" }[] = [
  {severity: "warning", field: "warnings"},
  {severity: "info", field: "infos"},
];

const groups = computed<Group[]>(() => {
  const result = new Map<string, Group>();
  for (const {severity, field} of SEVERITIES) {
    for (const d of (props.details?.[field] ?? []) as Diagnostic[]) {
      const key = `${severity}:${d.type}`;
      if (!result.has(key)) result.set(key, {key, severity, title: humanize(d.type ?? "message"), items: []});
      result.get(key)!.items.push(d);
    }
  }
  return [...result.values()];
});

const count = (severity: Severity) => groups.value.filter(g => g.severity === severity)
    .reduce((n, g) => n + g.items.length, 0);

// Number of shown items per group; long groups are revealed page by page
const shown = reactive<Record<string, number>>({});
const limit = (g: Group) => shown[g.key] ?? PAGE;

function humanize(type: string): string {
  const text = type.replace(/[-_]/g, " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/** HTML of a diagnostic kind the app knows, otherwise null */
function knownMessage(d: Diagnostic): string | null {
  const data = DIAGNOSTIC_DATA[d.type];
  if (!data) return null;
  try {
    return data.message(d);
  } catch {
    return null; // a stage logged the kind with other fields than the validation does
  }
}

/** Plain text for other diagnostics: their message, or their fields */
function fallbackMessage(d: Diagnostic): string {
  if (typeof d.msg === "string") return d.msg;
  return Object.entries(d)
      .filter(([k, v]) => k !== "type" && v !== null && v !== undefined)
      .map(([k, v]) => `${k}: ${typeof v === "object" ? JSON.stringify(v) : v}`)
      .join(" · ");
}
</script>

<template>
  <section v-if="groups.length" class="stage-diagnostics mt-4">
    <h5>
      Messages
      <small class="text-body-secondary fs-6">
        <template v-if="count('warning')">{{ count('warning') }} warning{{ count('warning') === 1 ? '' : 's' }}</template>
        <template v-if="count('warning') && count('info')">, </template>
        <template v-if="count('info')">{{ count('info') }} info{{ count('info') === 1 ? '' : 's' }}</template>
      </small>
    </h5>

    <details v-for="g in groups" :key="g.key" :class="g.severity === 'warning' ? 'alert-warning' : 'alert-info'"
             :open="g.items.length <= 5" class="alert py-2 mb-2">
      <summary>
        <i :class="g.severity === 'warning' ? 'fa-triangle-exclamation' : 'fa-circle-info'" class="fa me-1"></i>
        <strong>{{ g.title }}</strong>
        <span class="badge text-bg-light ms-2">{{ g.items.length }}</span>
      </summary>
      <ul class="mt-2 mb-0">
        <li v-for="(d, i) in g.items.slice(0, limit(g))" :key="i">
          <span v-if="knownMessage(d) !== null" v-html="knownMessage(d)"></span>
          <template v-else>{{ fallbackMessage(d) }}</template>
        </li>
      </ul>
      <button v-if="g.items.length > limit(g)" class="btn btn-sm btn-link px-0" type="button"
              @click="shown[g.key] = limit(g) + PAGE">
        Show more ({{ g.items.length - limit(g) }} remaining)
      </button>
    </details>
  </section>
</template>

<style scoped>
.stage-diagnostics summary {
  cursor: pointer;
}
</style>

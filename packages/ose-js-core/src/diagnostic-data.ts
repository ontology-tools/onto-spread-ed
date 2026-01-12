import {Diagnostic, DiagnosticKind, Severity} from "./model";

export const DIAGNOSTIC_DATA: Record<DiagnosticKind, {
    severity: Severity,
    title: (d: Diagnostic) => string,
    message: (d: Diagnostic) => string,
}> = {
    "unknown-parent": {
        severity: "error",
        title: d => `Unknown parent`,
        message: d => `The parent <code>${d.parent.label}</code> of <code>${
            (d.term ?? d.relation).label
        }</code>
              (<code>${(d.term ?? d.relation).id || 'no id'}</code>) is not known.`
    },
    "missing-parent": {
        severity: "error",
        title: d => `Missing parent`,
        message: d => `The parent <code>${ d.parent.label }</code> (<code>${ d.parent.id }</code>) of
              <code>${ d.term.label }</code>
              (<code>${
                d.term.id || ("no id")
              }</code>) is neither defined in the Excel files or imported.
              If it is an external term, add the missing import the entry with
              <code>${ d.parent.label } [${ d.parent.id }]</code>.`,
    },
    "no-parent": {
        severity: "error",
        title: d => `Term has no parent`,
        message: d => `The term <code>${d.term.label}</code> (<code>${d.term.id ?? 'no id'}</code>) has no parent!`,
    },
    "ignored-parent": {
        severity: "error",
        title: d => `${ d.status } parent`,
        message: d => `The parent <code>${ d.parent.label }</code> of <code>${ d.term.label }</code>
              (<code>${ d.term.id ?? 'no id' }</code>) is ${ d.status.toLowerCase() }.<br>`,
    },
    "missing-label": {
        severity: "error",
        title: d => `Missing label`,
        message: d => `The term <code>${ d.term.id }</code> has no label.`,
    },
    "missing-id": {
        severity: "error",
        title: d => `Term has no ID`,
        message: d => `              The term <code>${ d.term.label }</code> has no ID but is also not obsolete or pre-proposed. <br>`,
    },
    "unknown-disjoint": {
        severity: "error",
        title: d => `Unknown disjoint class`,
        message: d => `The class <code>${d.term.label}</code> (<code>${d.term.id ?? 'no id'}</code>) is
              specified to
              be disjoint with <code>${ d.disjoint_class.label }</code> but it is not known.<br>`,
    },
    "missing-disjoint": {
        severity: "error",
        title: d => `Missing disjoint class`,
        message: d => `The disjoint class <code>${ d.disjoint_class.label }</code> (<code>${ d.disjoint_class.id }</code>) of 
              <code>${ d.term.label }</code>
              (<code>${
                d.term.id || ("no id")
              }</code>) is neither defined in the Excel files or imported.
              If it is an external term, add the missing import the entry with
              <code>${ d.disjoint_class.label } [${ d.disjoint_class.id }]</code>.`,
    },
    "ignored-disjoint": {
        severity: "error",
        title: d => `${ d.status } disjoint class`,
        message: d => `The disjoint class <code>${ d.disjoint_class.label }</code> of <code>${ d.term.label }</code>
              (<code>${ d.term.id ?? 'no id' }</code>) is ${ d.status.toLowerCase() }.<br>`,
    },
    "unknown-relation-value": {
        severity: "error",
        title: d => `Unknown value for relation <code>${ d.relation.label }</code>`,
        message: d => `Related term <code>${ d.value.label }</code> of <code>${ d.term.label }</code>
              (<code>${
                d.term.id || "no id"
              }
            </code>) for <code>${ d.relation.label }</code> is not known.`,
    },
    "missing-relation-value": {
        severity: "error",
        title: d => `Unknown value for relation <code>${d.relation.label}</code>`,
        message: d => `Related term <code>${ d.value.label }</code> of 
              <code>${ d.term.label }</code>
              (<code>${
                d.term.id || ("no id")
              }</code>) is neither defined in the Excel files or imported.
              If it is an external term, add the missing import the entry with
              <code>${ d.value.label } [${ d.value.id }]</code>.`,
    },
    "ignored-relation-value": {
        severity: "error",
        title: d => `${ d.status } value for relation <code>${ d.relation.label }</code>`,
        message: d => `Related term <code>${ d.value.label }</code> of <code>${ d.term.label }</code>
              (<code>${ d.term.id ?? 'no id' }</code>) is ${ d.status.toLowerCase() }.`,
    },
    "unknown-range": {
        severity: "error",
        title: d => `Unknown range`,
        message: d => `The range <code>${ d.relation.range.label }</code> of
              <code>${ d.relation.label }</code>
              (<code>${
                d.relation.id || "no id"
              }
            </code>) is not known. `,
    },
    "missing-range": {
        severity: "error",
        title: d => `Missing range`,
        message: d => `The range <code>${ d.relation.range.label }</code> of 
              <code>${ d.relation.label }</code>
              (<code>${
                d.relation.id || ("no id")
              }</code>) is neither defined in the Excel files or imported.
              If it is an external term, add the missing import the entry with
              <code>${ d.range.label } [${ d.range.id }]</code>.`,
    },
    "ignored-range": {
        severity: "error",
        title: d => `${ d.status } range`,
        message: d => `The range <code>${ d.range.label }</code> of <code>${ d.relation.label }</code>
              (<code>${ d.relation.id ?? 'no id' }</code>) is ${ d.status.toLowerCase() }.<br>`,
    },
    "unknown-domain": {
        severity: "error",
        title: d => `Unknown domain`,
        message: d => `The domain <code>${ d.relation.domain.label }</code> of
              <code>${ d.relation.label }</code>
              (<code>${ d.relation.id || "no id" } </code>) is not known.`,
    },
    "missing-domain": {
        severity: "error",
        title: d => `Missing domain`,
        message: d => `The domain <code>${ d.relation.domain.label }</code> of 
              <code>${ d.relation.label }</code>
              (<code>${
                d.relation.id || ("no id")
              }</code>) is neither defined in the Excel files or imported.
              If it is an external term, add the missing import the entry with
              <code>${ d.domain.label } [${ d.domain.id }]</code>.`,
    },
    "ignored-domain": {
        severity: "error",
        title: d => `${ d.status } domain`,
        message: d => `The domain <code>${ d.domain.label }</code> of <code>${ d.relation.label }</code>
              (<code>${ d.relation.id ?? 'no id' }</code>) is ${ d.status.toLowerCase() }.<br>`,
    },
    "unknown-relation": {
        severity: "error",
        title: d => `Unknown relation`,
        message: d => `The relation ${d.relation.label ? (`<code>${d.relation.label}</code>` + (d.relation.id ? '(' + d.relation.id + ')' : '')) : d.relation.id} is not known`,
    },
    "duplicate": {
        severity: "error",
        title: d => `Conflicting entries (duplicates)`,
        message: d => `There are multiple terms for the ${ d.duplicate_field } <code>${ d.duplicate_value }</code>:`,
    },
    "incomplete-term": {
        severity: "warning",
        title: d => `Incomplete term`,
        message: d => `There is an incomplete term with no an ID, a label, or a parent defined. Is there an empty line in the
              spreadsheet? The line is ignored`,
    },
    "unknown-column": {
        severity: "warning",
        title: d => `Unmapped column`,
        message: d => `The column <code>${ d.column }</code> of <code>${ d.sheet }</code> is not mapped
              to any OWL property or internal field.`,
    },
    "missing-import": {
        severity: "warning",
        title: d => `Missing import`,
        message: d => `The term <code>${d.term.label}</code> (<code>${d.term.id ?? 'no id'}</code>) has the curation
              status
              "External" but is not included in the externally imported terms.` + (d.term.id ? ` Does the term still exist in
                ${ d.term.id.split(":")[0] }?` : ""),
    },
    "inconsistent-import": {
        severity: "warning",
        title: d => `Inconsistent import`,
        message: d => `The term <code>${d.term.label}</code> (<code>${d.term.id ?? 'no id'}</code>) has the curation
              status "External" but its ` +
            (d.term.id !== d.imported_term.id ? `ID (<code>${d.imported_term.id}</code>)` : `label (<code>${d.imported_term.label}</code>)`) +
            ` differs.`,
    },

}

"""Human-readable presentation of ose-lib diagnostics."""

from collections.abc import Mapping
from typing import Literal

import click

from ose.result import Message

type Severity = Literal["error", "warning", "info", "debug"]

COLORS: dict[Severity, str] = {"error": "red", "warning": "yellow", "info": "cyan", "debug": "bright_black"}
DESCRIPTIONS = {
    "no-parent": "Term has no parent.",
    "missing-label": "Entity has no label.",
    "missing-id": "Entity has no ID.",
    "unknown-parent": "Parent could not be resolved.",
    "missing-parent": "Parent is missing from the ontology.",
    "ignored-parent": "Parent has an ignored curation status.",
    "unknown-column": "Unrecognized spreadsheet column.",
    "duplicate": "Conflicting duplicate entities.",
}


def describe(value: object) -> str:
    """Summarize entities and diagnostic details without Python or JSON dumps."""
    if value is None:
        return "—"
    if isinstance(value, Mapping):
        identifier, label = value.get("id"), value.get("label")
        if identifier or label:
            return f"{label} [{identifier}]" if identifier and label else str(identifier or label)
        return "; ".join(f"{str(k).replace('_', ' ')}: {describe(v)}" for k, v in value.items())
    if isinstance(value, (list, tuple, set, frozenset)):
        return ", ".join(describe(item) for item in value) or "—"
    identifier, label = getattr(value, "id", None), getattr(value, "label", None)
    if identifier or label:
        return f"{label} [{identifier}]" if identifier and label else str(identifier or label)
    return str(value)


def format_diagnostic(diagnostic: Message, *, verbose: bool = False) -> str:
    kind = str(diagnostic.get("type", "diagnostic"))
    subject_key = "term" if diagnostic.get("term") else "relation"
    subject = diagnostic.get(subject_key)
    origin = diagnostic.get("origin") or diagnostic.get("file") or diagnostic.get("sheet")
    row = diagnostic.get("row")
    if not origin and subject is not None:
        origin = subject.get("origin") if isinstance(subject, Mapping) else getattr(subject, "origin", None)
    if isinstance(origin, (tuple, list)):
        if len(origin) > 1 and row is None:
            row = origin[1]
        origin = origin[0] if origin else None
    location = str(origin) if origin else ""
    if row is not None:
        location += f":{row}" if location else f"row {row}"
    if diagnostic.get("column") is not None:
        location += f" (column {diagnostic['column']})"
    description = diagnostic.get("msg") or DESCRIPTIONS.get(kind) or kind.replace("-", " ").capitalize()
    parts = [f"[{kind}]", *(p for p in (location, describe(subject) if subject else "") if p), str(description)]
    summary = ": ".join(parts)
    hidden = {"type", "msg", "origin", "file", "sheet", "row", "column", subject_key, "traceback"}
    details = [
        f"  {key.replace('_', ' ').capitalize()}: {describe(value)}"
        for key, value in diagnostic.items()
        if key not in hidden and value is not None
    ]
    if verbose and diagnostic.get("traceback"):
        details.extend(f"  {line}" for line in str(diagnostic["traceback"]).rstrip().splitlines())
    return "\n".join([summary, *details])


def format_state(state: str) -> str:
    color = (
        "green"
        if state in {"completed", "valid"}
        else ("red" if state in {"failed", "errored", "cancelled", "invalid"} else "yellow")
    )
    return click.style(state, fg=color, bold=True)

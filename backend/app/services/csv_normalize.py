from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

# Canonical fields we want internally
CANON = ["item_id", "name", "cost", "value", "category", "risk"]

# Common real-world aliases
ALIASES: dict[str, set[str]] = {
    "item_id": {"item_id", "id", "itemid", "item", "key", "uuid", "project_code"},
    "name": {"name", "item_name", "project", "project_name", "title", "initiative", "initiative_name"},
    "cost": {"cost", "price", "expense", "budget", "capex", "opex", "amount", "effort", "hours", "estimated_cost_usd"},
    "value": {"value", "benefit", "impact", "impact_score", "roi", "score", "priority", "utility", "expected_annual_value_usd"},
    "category": {"category", "type", "team", "department", "group"},
    "risk": {"risk", "probability", "uncertainty", "volatility", "risk_score"},
}

def _norm_header(s: str) -> str:
    # Lowercase and drop non-alphanumerics to match "Project Name", "project_name", etc.
    s = s.replace("\u00A0", " ")  # NBSP -> space
    s = s.lstrip("\ufeff").strip().lower()  # BOM + surrounding whitespace
    s = re.sub(r"[\s\-]+", "_", s)
    s = re.sub(r"[^a-z0-9_]", "", s)
    return s

@dataclass(frozen=True)
class ColumnResolution:
    original_columns: list[str]          # as seen in the file
    normalized_columns: list[str]        # normalized names
    mapping: dict[str, str]              # canon -> original column name
    missing_required: list[str]          # missing among ["name","cost","value"]
    warnings: list[str]


REQUIRED = {"name", "cost", "value"}


def resolve_columns(fieldnames: Iterable[str]) -> ColumnResolution:
    original = [c for c in fieldnames if c is not None]
    normalized = [_norm_header(c) for c in original]

    # Build map: normalized -> original
    norm_to_orig: dict[str, str] = {}
    for orig, norm in zip(original, normalized, strict=True):
        # first ones win if duplicates
        norm_to_orig.setdefault(norm, orig)

    # Try to resolve each canon field
    mapping: dict[str, str] = {}
    warnings: list[str] = []

    for canon, alias_set in ALIASES.items():
        found = []
        for alias in alias_set:
            alias_norm = _norm_header(alias)
            if alias_norm in norm_to_orig:
                found.append(norm_to_orig[alias_norm])

        if len(found) == 1:
            mapping[canon] = found[0]
        elif len(found) > 1:
            # ambiguous — don't auto-pick
            warnings.append(f"Ambiguous columns for '{canon}': {found}. Using none (will require mapping UI later).")

    missing = [c for c in sorted(REQUIRED) if c not in mapping]

    # Friendly warning if item_id missing (we'll auto-generate in 1B)
    if "item_id" not in mapping:
        warnings.append("No item_id column found. IDs will be auto-generated (I1, I2, ...).")

    return ColumnResolution(
        original_columns=original,
        normalized_columns=normalized,
        mapping=mapping,
        missing_required=missing,
        warnings=warnings,
    )

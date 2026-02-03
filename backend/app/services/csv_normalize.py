from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

# Canonical fields we want internally
CANON = ["item_id", "name", "cost", "value", "category", "risk"]

# Common real-world aliases
ALIASES: dict[str, set[str]] = {
    "item_id": {"item_id", "id", "itemid", "item", "key", "uuid"},
    "name": {"name", "item_name", "project", "project_name", "title", "initiative"},
    "cost": {"cost", "price", "expense", "budget", "capex", "opex", "amount", "effort", "hours"},
    "value": {"value", "benefit", "impact", "impact_score", "roi", "score", "priority", "utility"},
    "category": {"category", "type", "team", "department", "group"},
    "risk": {"risk", "probability", "uncertainty", "volatility"},
}

def _norm_header(s: str):
    # Lowercase and drop non-alphanumerics to match "Project Name", "project_name", etc.
    s = s.strip().lower()
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


def resolve_columns(fieldnames: Iterable[str]):
    original = [c.strip() for c in fieldnames if c is not None]
    normalized = [_norm_header(c) for c in original]

    # Build map: normalized -> original
    norm_to_orig: dict[str, str] = {}
    for orig, norm in zip(original, normalized):
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
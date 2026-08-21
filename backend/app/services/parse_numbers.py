from __future__ import annotations

import re

_CURRENCY = re.compile(r"[₹$€£,]") # strip commas and common currenycy symbols


def parse_float(x: float | int | str | None, *, default: float | None = None) -> float | None:
    if x is None:
        return default
    if isinstance(x, (int, float)):
        return float (x)
    s = str(x).strip()
    if s == "":
        return default
    s = _CURRENCY.sub("", s)
    # handle "1 200" style spaces
    s = s.replace(" ", "")
    try:
        return float(s)
    except ValueError:
        return default

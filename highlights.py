"""
highlights.py — select homepage highlight entries from talks.json

Heuristic (configured via constants below):
  1. Exclude any entry with exclude_from_highlights == true
  2. Exclude entries whose date falls outside the WINDOW_MONTHS rolling window
     (entries with partial dates like "2025" or "2025-06" are included if they
     plausibly fall within the window — a year-only date is treated as YYYY-07-01,
     a year-month date as YYYY-MM-15)
  3. From the remaining candidates, apply per-tag caps (most recent first):
       new  → MAX_NEW
       talk → MAX_TALK
       role → MAX_ROLE
       phd  → MAX_PHD
  4. Merge the selected entries and sort by date descending
  5. Return at most MAX_TOTAL entries
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path


# ── Configuration ────────────────────────────────────────────────────────────

WINDOW_MONTHS: int = 18   # rolling look-back window
MAX_NEW:   int = 3
MAX_TALK:  int = 2
MAX_ROLE:  int = 1
MAX_PHD:   int = 1
MAX_TOTAL: int = 6


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_date(date_str: str) -> date:
    """
    Parse a flexible date string into a date object for comparison.
    Supported formats: YYYY, YYYY-MM, YYYY-MM-DD.
    Partial dates are padded so they sort conservatively inside the window.
    """
    parts = str(date_str).strip().split("-")
    if len(parts) == 3:
        return date(int(parts[0]), int(parts[1]), int(parts[2]))
    if len(parts) == 2:
        return date(int(parts[0]), int(parts[1]), 15)   # mid-month
    return date(int(parts[0]), 7, 1)                    # mid-year


def select_highlights(talks: list[dict], today: date | None = None) -> list[dict]:
    """
    Given the full list of talk/highlight entries (loaded from talks.json),
    return the ordered list of entries to display in the homepage highlights panel.

    Parameters
    ----------
    talks : list[dict]
        All entries from content/talks.json.
    today : date, optional
        Override "today" for deterministic testing. Defaults to date.today().

    Returns
    -------
    list[dict]
        Up to MAX_TOTAL entries, sorted by date descending.
    """
    if today is None:
        today = date.today()

    cutoff = today - timedelta(days=WINDOW_MONTHS * 30)

    # Step 1 & 2 — filter out excluded entries and those outside the window
    candidates = [
        entry for entry in talks
        if not entry.get("exclude_from_highlights", False)
        and _parse_date(entry["date"]) >= cutoff
    ]

    # Step 3 — sort candidates newest-first, then apply per-tag caps
    candidates.sort(key=lambda e: _parse_date(e["date"]), reverse=True)

    caps = {"new": MAX_NEW, "talk": MAX_TALK, "role": MAX_ROLE, "phd": MAX_PHD}
    counts: dict[str, int] = {tag: 0 for tag in caps}
    selected: list[dict] = []

    for entry in candidates:
        tag = entry.get("tag", "")
        if tag not in caps:
            continue
        if counts[tag] < caps[tag]:
            selected.append(entry)
            counts[tag] += 1

    # Step 4 & 5 — re-sort and cap total
    selected.sort(key=lambda e: _parse_date(e["date"]), reverse=True)
    return selected[:MAX_TOTAL]


# ── Standalone test ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    talks_path = Path(__file__).parent / "content" / "talks.json"
    talks = json.loads(talks_path.read_text(encoding="utf-8"))
    highlights = select_highlights(talks)
    print(f"Selected {len(highlights)} highlight(s):\n")
    for h in highlights:
        print(f"  [{h['tag'].upper():4s}]  {h['date']}  {h['title']}")

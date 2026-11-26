"""
In-memory case store for AutoDecodeX.

Storage strategy: Python dict keyed by case_id, held for the lifetime of
the FastAPI process.

Documented limitations:
  - Cases do NOT survive a process restart or redeploy.
  - There is no authentication; any client that can reach the API can read
    any case by its ID.
  - This is suitable for single-user local deployments and CTF workflows.
  - For multi-user or persistent deployments, replace with a database backend
    (SQLite via SQLModel is the recommended lightweight upgrade).
  - Maximum stored cases: configurable via MAX_CASES (default 1000).
    Oldest cases are evicted when the limit is reached.
"""
from __future__ import annotations

import threading
from collections import OrderedDict
from typing import Optional

from backend.models.schemas import Case

MAX_CASES = int(1000)

# Thread-safe ordered dict (insertion order = creation order)
_store: OrderedDict[str, Case] = OrderedDict()
_lock = threading.Lock()


def save_case(case: Case) -> Case:
    """Persist or update a case. Evicts oldest if at capacity."""
    with _lock:
        if len(_store) >= MAX_CASES and case.case_id not in _store:
            # Evict oldest
            _store.popitem(last=False)
        _store[case.case_id] = case
    return case


def get_case(case_id: str) -> Optional[Case]:
    """Retrieve a case by ID. Returns None if not found."""
    with _lock:
        return _store.get(case_id)


def list_cases(limit: int = 50, offset: int = 0) -> list[Case]:
    """Return cases in reverse-creation order (most recent first)."""
    with _lock:
        items = list(_store.values())
    items.reverse()
    return items[offset : offset + limit]


def search_cases(
    query: Optional[str] = None,
    format_filter: Optional[str] = None,
    min_findings: Optional[int] = None,
    sort_by: str = "created_at",
    descending: bool = True,
    limit: int = 50,
    offset: int = 0
) -> list[Case]:
    """
    Search and filter stored cases with sorting and pagination.
    Supports substring match across filename, case_id, sha256, and format.
    """
    with _lock:
        items = list(_store.values())

    filtered = []
    q = query.strip().lower() if query else None
    fmt = format_filter.strip().lower() if format_filter else None

    for c in items:
        if q:
            matches_q = (
                q in c.case_id.lower()
                or q in c.original_filename.lower()
                or q in c.sha256.lower()
                or (c.detected_format and q in c.detected_format.lower())
            )
            if not matches_q:
                continue

        if fmt:
            if not c.detected_format or fmt not in c.detected_format.lower():
                continue

        if min_findings is not None:
            if len(c.findings) < min_findings:
                continue

        filtered.append(c)

    # Sorting
    if sort_by == "file_size":
        filtered.sort(key=lambda x: x.file_size_bytes, reverse=descending)
    elif sort_by == "findings_count":
        filtered.sort(key=lambda x: len(x.findings), reverse=descending)
    elif sort_by == "filename":
        filtered.sort(key=lambda x: x.original_filename.lower(), reverse=descending)
    else:  # default to created_at
        filtered.sort(key=lambda x: str(x.created_at), reverse=descending)

    return filtered[offset : offset + limit]


def get_case_summary_stats() -> dict:
    """Computes high-level aggregated metrics across all stored cases."""
    with _lock:
        items = list(_store.values())

    total_bytes = sum(c.file_size_bytes for c in items)
    total_findings = sum(len(c.findings) for c in items)
    formats = {}
    for c in items:
        fmt = c.detected_format or "Unknown"
        formats[fmt] = formats.get(fmt, 0) + 1

    return {
        "total_cases": len(items),
        "total_evidence_bytes": total_bytes,
        "total_findings": total_findings,
        "format_breakdown": formats,
    }


def clear_cases() -> int:
    """Clear all stored cases. Returns count of evicted cases."""
    with _lock:
        count = len(_store)
        _store.clear()
        return count


def delete_case(case_id: str) -> bool:
    """Remove a case. Returns True if it existed."""
    with _lock:
        if case_id in _store:
            del _store[case_id]
            return True
    return False


def case_count() -> int:
    with _lock:
        return len(_store)

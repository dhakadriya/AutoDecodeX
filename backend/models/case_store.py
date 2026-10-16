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

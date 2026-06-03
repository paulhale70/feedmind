"""Pytest bootstrap.

The test modules live in tests/ but import the application modules
(rss_core, rss_database_v3, ...) from the repo root. Pytest's default import
mode only puts the test file's own directory on sys.path, so `pytest tests/`
would fail with ModuleNotFoundError without this shim. Placing conftest.py at
the repo root also makes pytest add the root to sys.path automatically; the
explicit insert below keeps it working regardless of import mode.

It also reconfigures stdout to UTF-8 so the tests' ✓/✗/emoji output doesn't
crash on Windows consoles using the legacy cp1252 code page.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (ValueError, OSError):
        pass

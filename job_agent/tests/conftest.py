"""Shared pytest configuration for job-agent tests."""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is on the path for all tests
_src = Path(__file__).parent.parent / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

"""
conftest.py — Root-level pytest configuration.
Adds simulator and api to sys.path before any test is collected.
"""
import sys
import os

ROOT = os.path.dirname(__file__)
for _sub in ('simulator', 'api'):
    _p = os.path.join(ROOT, _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)

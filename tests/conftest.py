"""
tests/conftest.py
Adds simulator and api directories to sys.path for unit testing.
This conftest is loaded by pytest before any test collection.
"""
import sys
import os

# Root project directory
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Add simulator and api directories so 'from app.xxx import ...' works
for _sub in ('simulator', 'api'):
    _path = os.path.join(ROOT, _sub)
    if _path not in sys.path:
        sys.path.insert(0, _path)

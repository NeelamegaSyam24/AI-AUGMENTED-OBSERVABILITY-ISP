"""
tests/unit/conftest.py
For ML tests, api must come BEFORE simulator on sys.path
so that 'app.ml' resolves to api/app/ml, not simulator/app.
"""
import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
_api_path = os.path.join(ROOT, 'api')
_sim_path = os.path.join(ROOT, 'simulator')

# Insert api FIRST so app.ml resolves to api/app/ml
if _api_path not in sys.path:
    sys.path.insert(0, _api_path)
if _sim_path not in sys.path:
    sys.path.insert(1, _sim_path)

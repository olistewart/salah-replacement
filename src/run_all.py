"""
Runs every numbered script in this folder in order, in one shared namespace --
each script picks up where the previous one left off, exactly like running
the original notebook's cells top to bottom.

Usage:
    python src/run_all.py

Note: 02_data_collection.py hits the live Understat API and 12_transfermarkt.py
hits Transfermarkt (which blocked scripted access in the original run -- see
that file's docstring). Both are slow/network-dependent by nature. Everything
from 03 onward is pure computation over the cached CSVs in DATA_DIR.
"""
import pathlib
import runpy

SCRIPT_DIR = pathlib.Path(__file__).parent
scripts = sorted(p for p in SCRIPT_DIR.glob("[0-9][0-9]_*.py"))

shared_globals: dict = {}
for script in scripts:
    print(f"\n{'=' * 80}\nRunning {script.name}\n{'=' * 80}")
    shared_globals = runpy.run_path(str(script), init_globals=shared_globals)

print("\nDone. Outputs are in DATA_DIR (see 01_setup.py).")

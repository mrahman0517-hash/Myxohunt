"""Let the tests import the simulation files (settings.py, grids.py, …) from the folder above."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

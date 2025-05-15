import sys
import os
# Gör så att src/ hamnar i PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
# Inga trasiga import-satser kvar här.

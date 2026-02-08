"""
Tools test package initialization.

This file ensures that imports from parent test directory work correctly.
"""
import sys
from pathlib import Path

# Add parent tests directory to path so we can import test_adapter and test_data
tests_dir = Path(__file__).parent.parent
if str(tests_dir) not in sys.path:
    sys.path.insert(0, str(tests_dir))

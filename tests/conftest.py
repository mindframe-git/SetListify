"""Pytest configuration."""

import sys
from pathlib import Path

# Add src directory to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

pytest_plugins = []

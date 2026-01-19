#!/usr/bin/env python3
"""Startup wrapper for Clever Cloud deployment.

This script ensures the correct Python path is set before importing the main module.
"""

import sys
from pathlib import Path

# Add the lf-automator directory to Python path
app_dir = Path(__file__).parent / "lf-automator"
sys.path.insert(0, str(app_dir))

# Now import and run the main module
from main import main

if __name__ == "__main__":
    sys.exit(main())

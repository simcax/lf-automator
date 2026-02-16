#!/bin/bash
# Wrapper script for Token Inventory Tracking system
# This script sets up the environment and runs the main.py entry point

# Set PYTHONPATH to include the lf-automator directory
export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}$(dirname "$0")/lf-automator"

# Run the main.py script with all provided arguments
python "$(dirname "$0")/lf-automator/main.py" "$@"

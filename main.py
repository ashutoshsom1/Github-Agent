#!/usr/bin/env python3
"""
GitHub Agent AI (OctoAgent)
Main entrypoint for CLI, analysis workflows, and MCP server.
"""

import sys
import os

# Ensure UTF-8 stdout encoding on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add src to Python module path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from github_agent.cli import cli

def run():
    # Backwards compatibility: if invoked directly with --keyword or -k, route to 'scan'
    if len(sys.argv) > 1 and sys.argv[1] in ("--keyword", "-k"):
        sys.argv.insert(1, "scan")
    cli()

if __name__ == "__main__":
    run()

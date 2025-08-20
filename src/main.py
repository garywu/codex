#!/usr/bin/env python3

import sys
from pathlib import Path

# Add codex to path
sys.path.insert(0, str(Path(__file__).parent.parent / "codex"))

from codex.cli import main

if __name__ == "__main__":
    main()

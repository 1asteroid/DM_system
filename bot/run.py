#!/usr/bin/env python
"""Bot launch script — run from project root OR from bot/ directory."""
import sys
import asyncio
from pathlib import Path

# Ensure project root is on the path
_root = Path(__file__).parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from bot.main import main

if __name__ == "__main__":
    asyncio.run(main())

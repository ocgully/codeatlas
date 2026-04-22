"""Allow `python -m codemap` invocation."""
import sys
from codemap.cli import main

if __name__ == "__main__":
    sys.exit(main())

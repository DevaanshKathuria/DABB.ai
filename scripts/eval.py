"""CLI wrapper for model evaluation."""

from __future__ import annotations

import sys

from contract_risk.cli import main


if __name__ == "__main__":
    sys.argv.insert(1, "eval")
    main()

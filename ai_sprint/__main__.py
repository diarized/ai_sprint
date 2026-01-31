"""Entry point for python -m ai_sprint."""

import sys
from ai_sprint.cli.main import cli


def main() -> int:
    """Run the CLI."""
    try:
        cli()
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from pipeline import ensure_directories, run_pipeline

load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the IdeaBee pipeline")
    parser.add_argument("idea", nargs="?", default=os.getenv("IDEABEE_SAMPLE_IDEA", "An AI startup builder that turns rough ideas into validated ventures."))
    args = parser.parse_args()

    ensure_directories()
    result = run_pipeline(args.idea)
    print(json.dumps(result["delivery"], indent=2))


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json
import os

from dotenv import load_dotenv

from pipeline import ensure_directories, run_pipeline

load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the IdeaBee pipeline")
    parser.add_argument(
        "idea",
        nargs="?",
        default=os.getenv(
            "IDEABEE_SAMPLE_IDEA",
            "An AI startup builder that turns rough ideas into validated ventures.",
        ),
    )
    parser.add_argument("--output-dir", default=os.getenv("OUTPUT_DIR", "outputs"))
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use local fallbacks only; skip OpenRouter, Hugging Face, Tavily, and DuckDuckGo.",
    )
    args = parser.parse_args()

    if args.offline:
        os.environ["IDEABEE_OFFLINE"] = "1"

    ensure_directories()
    print("Running IdeaBee pipeline...")
    result = run_pipeline(args.idea, output_dir=args.output_dir)

    summary = {
        "quality_score": result["delivery"].get("quality_score"),
        "checks": result["delivery"].get("checks", []),
        "website_bundle": result["website"].get("bundle"),
        "pptx": result["pitch"].get("pptx"),
        "pdf": result["pitch"].get("pdf"),
        "delivery_zip": result["delivery"].get("package"),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

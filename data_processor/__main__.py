"""data_processor CLI.

    python -m data_processor                      # process what the ingestor persisted
    python -m data_processor --limit 3            # only 3 locations
    python -m data_processor --groups 16          # 16 varied groups per location
    python -m data_processor --transport mock     # no real model (demo/CI)
"""

from __future__ import annotations

import argparse
import logging

from . import run


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic audience from the ingested data.")
    parser.add_argument("--limit", type=int, default=None, help="maximum number of locations to process")
    parser.add_argument("--groups", type=int, default=12, help="varied audience groups per location")
    parser.add_argument(
        "--transport",
        default="",
        choices=["", "auto", "dapr", "http", "mock"],
        help="LLM transport (default: env LLM_TRANSPORT or auto)",
    )
    parser.add_argument("--no-persist", action="store_true", help="do not write output files")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    specs = run(
        limit=args.limit,
        max_groups=args.groups,
        transport=args.transport,
        persist=not args.no_persist,
    )

    for spec in specs:
        scores = spec.get("audience_scores", {})
        top = ", ".join(
            f"{m}~{v['expected_avg']}" for m, v in list(scores.items())[:4] if v.get("expected_avg") is not None
        )
        print(
            f"[{spec['zip_code']}] {spec['location_label']}: "
            f"{spec['n_audience_groups']} groups, {spec['n_field_groups']} topics | {top}"
        )


if __name__ == "__main__":
    main()

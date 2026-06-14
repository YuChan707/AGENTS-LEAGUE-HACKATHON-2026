"""CLI del data_processor.

    python -m data_processor                      # procesa lo persistido por el ingestor
    python -m data_processor --limit 3            # solo 3 ubicaciones
    python -m data_processor --groups 16          # 16 grupos variados por ubicacion
    python -m data_processor --transport mock     # sin modelo real (demo/CI)
"""

from __future__ import annotations

import argparse
import logging

from . import run


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera audiencia sintetica desde la data ingerida.")
    parser.add_argument("--limit", type=int, default=None, help="numero maximo de ubicaciones a procesar")
    parser.add_argument("--groups", type=int, default=12, help="grupos de audiencia variados por ubicacion")
    parser.add_argument(
        "--transport",
        default="",
        choices=["", "auto", "dapr", "http", "mock"],
        help="transporte del LLM (default: env LLM_TRANSPORT o auto)",
    )
    parser.add_argument("--no-persist", action="store_true", help="no escribir archivos de salida")
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
            f"{spec['n_audience_groups']} grupos, {spec['n_field_groups']} temas | {top}"
        )


if __name__ == "__main__":
    main()

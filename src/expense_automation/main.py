import argparse
from pathlib import Path
from typing import List, Dict, Any

from .io_utils import load_receipts, load_external_charges, export_to_csv
from .processor import match_receipts_with_external


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Merge OCR receipts with external CSV/Excel-like data to generate a Tina Claim Form-compatible report.",
    )
    parser.add_argument(
        "receipts",
        type=Path,
        help="Path to OCR receipts JSON file.",
    )
    parser.add_argument(
        "external",
        type=Path,
        help="Path to external CSV data (e.g., ETC, charging).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/claim_form.csv"),
        help="Output CSV path for the generated claim form.",
    )
    return parser


def generate_report(receipts_path: Path, external_path: Path, output_path: Path) -> Path:
    receipts = load_receipts(receipts_path)
    external = load_external_charges(external_path)
    merged_rows: List[Dict[str, Any]] = match_receipts_with_external(receipts, external)

    export_to_csv(merged_rows, output_path)
    return output_path


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    output_path = generate_report(args.receipts, args.external, args.output)
    print(f"Claim form generated at {output_path}")


if __name__ == "__main__":
    main()

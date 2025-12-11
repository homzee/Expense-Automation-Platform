import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Dict, Any, Tuple

DateKey = Tuple[str, str]

REQUIRED_RECEIPT_FIELDS = {"receipt_id", "date", "plate", "merchant", "amount", "category"}
REQUIRED_EXTERNAL_FIELDS = {"plate", "date", "source", "amount", "note"}


def _parse_date(value: str) -> str:
    """Normalize date to YYYY-MM-DD string."""
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date().isoformat()
    except ValueError as exc:
        raise ValueError(f"Invalid date '{value}'. Expected YYYY-MM-DD.") from exc


def load_receipts(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Receipt payload must be a list of objects.")

    receipts: List[Dict[str, Any]] = []
    for idx, raw in enumerate(data, start=1):
        if not REQUIRED_RECEIPT_FIELDS.issubset(raw):
            missing = REQUIRED_RECEIPT_FIELDS - set(raw)
            raise ValueError(f"Receipt #{idx} is missing fields: {sorted(missing)}")

        normalized = {
            "receipt_id": str(raw["receipt_id"]).strip(),
            "date": _parse_date(str(raw["date"])),
            "plate": str(raw["plate"]).strip(),
            "merchant": str(raw["merchant"]).strip(),
            "amount": float(raw["amount"]),
            "category": str(raw["category"]).strip(),
        }
        receipts.append(normalized)
    return receipts


def load_external_charges(path: Path) -> Dict[DateKey, List[Dict[str, Any]]]:
    if not path.exists():
        raise FileNotFoundError(f"External data file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not REQUIRED_EXTERNAL_FIELDS.issubset(reader.fieldnames):
            raise ValueError(
                f"CSV must contain columns: {sorted(REQUIRED_EXTERNAL_FIELDS)}"
            )

        charges: Dict[DateKey, List[Dict[str, Any]]] = {}
        for idx, row in enumerate(reader, start=2):  # header is line 1
            try:
                normalized_date = _parse_date(row["date"])
                record = {
                    "plate": row["plate"].strip(),
                    "date": normalized_date,
                    "source": row["source"].strip(),
                    "amount": float(row["amount"]),
                    "note": row.get("note", "").strip(),
                }
            except Exception as exc:  # noqa: BLE001
                raise ValueError(f"Invalid row at line {idx}: {row}") from exc

            key: DateKey = (record["plate"], record["date"])
            charges.setdefault(key, []).append(record)
    return charges


def ensure_output_directory(path: Path) -> None:
    target_dir = path.parent
    target_dir.mkdir(parents=True, exist_ok=True)


def export_to_csv(records: Iterable[Dict[str, Any]], output_path: Path) -> None:
    ensure_output_directory(output_path)
    records = list(records)
    if not records:
        output_path.write_text("", encoding="utf-8")
        return

    fieldnames = list(records[0].keys())
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

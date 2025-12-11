from typing import Dict, List, Any, Tuple, Iterable

from .io_utils import DateKey


def match_receipts_with_external(
    receipts: List[Dict[str, Any]],
    external: Dict[DateKey, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """Merge OCR receipts with external CSV data.

    Matching is performed on (plate, date). If multiple external rows match the same
    key, they are consumed in order, so repeated receipts for the same day will
    still be paired deterministically.
    """

    # Copy the external map so we can pop matched rows without mutating caller data
    external_pool: Dict[DateKey, List[Dict[str, Any]]] = {
        key: list(rows) for key, rows in external.items()
    }

    merged: List[Dict[str, Any]] = []
    for receipt in receipts:
        key: DateKey = (receipt["plate"], receipt["date"])
        external_rows = external_pool.get(key, [])
        matched_row = external_rows.pop(0) if external_rows else None
        if external_rows:
            external_pool[key] = external_rows
        elif key in external_pool:
            # Remove empty list to keep unmatched clean
            external_pool.pop(key, None)

        merged.append(
            {
                "receipt_id": receipt["receipt_id"],
                "date": receipt["date"],
                "plate": receipt["plate"],
                "category": receipt["category"],
                "merchant": receipt["merchant"],
                "receipt_amount": receipt["amount"],
                "external_amount": matched_row.get("amount") if matched_row else None,
                "external_source": matched_row.get("source") if matched_row else None,
                "external_note": matched_row.get("note") if matched_row else None,
                "final_amount": matched_row.get("amount") if matched_row else receipt["amount"],
                "match_status": "matched" if matched_row else "unmatched",
            }
        )

    for leftover in unmatched_external_rows(external_pool):
        merged.append(
            {
                "receipt_id": None,
                "date": leftover["date"],
                "plate": leftover["plate"],
                "category": None,
                "merchant": None,
                "receipt_amount": None,
                "external_amount": leftover.get("amount"),
                "external_source": leftover.get("source"),
                "external_note": leftover.get("note"),
                "final_amount": leftover.get("amount"),
                "match_status": "external_only",
            }
        )

    return merged


def unmatched_external_rows(external_pool: Dict[DateKey, List[Dict[str, Any]]]) -> Iterable[Dict[str, Any]]:
    """Flatten remaining external rows that were never matched."""
    for rows in external_pool.values():
        for row in rows:
            yield row

"""Data ingestion utilities for OCR mocks and Excel sources."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Iterable, List

import pandas as pd

from .models import ClaimHeader, ExpenseItem, parse_date


def get_mock_ocr_data(num_items: int = 5) -> list[dict]:
    """Generate mock OCR-style dictionaries for demonstration purposes."""

    # 使用固定起始日期模拟 OCR 识别结果，便于分页与排序测试
    base_date = date(2025, 9, 1)
    data: list[dict] = []
    for idx in range(num_items):
        item_date = base_date + timedelta(days=idx)
        data.append(
            {
                "transaction_date": item_date.isoformat(),
                "supplier_name": "Zaoh Japan",
                "invoice_no": f"OCR-{1000 + idx}",
                "expense_type": "Hotel",
                "description": "Business Trip Stay",
                "currency": "JPY",
                "original_amount": "18920",  # mirrors the example in the report
                "forex_rate": "0.0087",
                "gst_amount": "0",
            }
        )
    return data


class ExcelSourceReader:
    """Generic Excel adapter that maps tabular data into :class:`ExpenseItem` objects."""

    def __init__(self, file_path: str, column_mapping: dict, static_fields: dict):
        self.file_path = file_path
        self.column_mapping = column_mapping
        self.static_fields = static_fields

    def read(self) -> List[ExpenseItem]:
        try:
            df = pd.read_excel(self.file_path)
        except FileNotFoundError:
            print(f"Warning: Source file {self.file_path} not found. Skipping.")
            return []

        items: List[ExpenseItem] = []
        for _, row in df.iterrows():
            item_data: dict = {}
            # 通过列映射将 Excel 字段转换为模型字段
            for excel_col, model_field in self.column_mapping.items():
                if excel_col in row:
                    value = row[excel_col]
                    if isinstance(value, pd.Timestamp):
                        value = value.date()
                    item_data[model_field] = value

            for field, val in self.static_fields.items():
                item_data.setdefault(field, val)

            item_data.setdefault("invoice_no", "E-Receipt")
            item_data.setdefault("currency", "SGD")
            item_data.setdefault("forex_rate", Decimal("1.0"))

            try:
                tx_date = item_data.get("transaction_date")
                if tx_date:
                    item_data["transaction_date"] = parse_date(tx_date)

                expense_item = ExpenseItem(**item_data)
                expense_item.compute_financials()
                items.append(expense_item)
            except Exception as exc:  # pragma: no cover - defensive logging path
                print(f"Error parsing row {row}: {exc}")

        return items


def merge_expenses(*sources: Iterable[ExpenseItem]) -> list[ExpenseItem]:
    """Return a single sorted list of expenses by transaction date."""

    merged: list[ExpenseItem] = [item for source in sources for item in source]
    return sorted(merged, key=lambda item: item.transaction_date)

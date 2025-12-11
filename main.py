"""Runnable entrypoint demonstrating the expense automation pipeline.

The script stitches together OCR-like data, structured Excel sources, and the
Excel writer. It avoids failing when the template is absent, printing a helpful
hint instead. Replace ``template.xlsx`` with your blank claim form to generate
real output.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from expense_automation.ingestion import ExcelSourceReader, get_mock_ocr_data, merge_expenses
from expense_automation.models import ClaimHeader, ExpenseItem
from expense_automation.writer import ClaimFormWriter


def build_mock_items() -> list[ExpenseItem]:
    # 演示用 OCR 数据集合，模拟跨币种场景
    ocr_raw = get_mock_ocr_data(num_items=12)
    ocr_items: list[ExpenseItem] = []
    for row in ocr_raw:
        item = ExpenseItem(**row)
        item.compute_financials()
        ocr_items.append(item)
    return ocr_items


def build_excel_items() -> tuple[list[ExpenseItem], list[ExpenseItem]]:
    # Excel 读取器根据列映射和静态字段生成本地费用项
    etc_reader = ExcelSourceReader(
        file_path="source_etc.xlsx",
        column_mapping={
            "Transaction Date": "transaction_date",
            "Gantry Location": "description",
            "Amount": "original_amount",
        },
        static_fields={
            "supplier_name": "LTA (ETC)",
            "expense_type": "Transport",
            "invoice_no": "ETC-Statement",
            "currency": "SGD",
            "forex_rate": Decimal("1.0"),
        },
    )

    charging_reader = ExcelSourceReader(
        file_path="source_charging.xlsx",
        column_mapping={
            "Date": "transaction_date",
            "Station": "description",
            "Cost": "original_amount",
        },
        static_fields={
            "supplier_name": "EV Charging",
            "expense_type": "Fuel/Transport",
            "currency": "SGD",
            "forex_rate": Decimal("1.0"),
        },
    )

    return etc_reader.read(), charging_reader.read()


def main() -> None:
    ocr_items = build_mock_items()
    etc_items, charging_items = build_excel_items()

    all_items = merge_expenses(ocr_items, etc_items, charging_items)
    print(
        f"Prepared {len(all_items)} items (OCR: {len(ocr_items)}, "
        f"ETC: {len(etc_items)}, Charging: {len(charging_items)})"
    )

    header = ClaimHeader(
        employee_name="WANG TING I",
        department="Sales Engineer",
        month_of_claim="September",
    )

    template_path = Path("template.xlsx")
    if not template_path.exists():
        print(
            "Template not found. Please place your blank claim form at "
            f"{template_path.resolve()} and rerun."
        )
        return

    writer = ClaimFormWriter(template_path=str(template_path), output_path="Final_Claim_Report.xlsx")
    writer.process(header, all_items)
    print("Claim form generated: Final_Claim_Report.xlsx")


if __name__ == "__main__":
    main()

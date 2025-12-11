# Expense-Automation-Platform

An automated reimbursement generator that merges OCR-parsed receipt data with external sources (ETC, charging fees) to produce fully formatted reimbursement forms. The current lightweight implementation avoids third-party dependencies so it runs in locked-down environments and outputs an Excel-compatible CSV claim form.

## Getting started

1. **Inspect sample data** (already included):
   - `data/receipts_ocr.json` – OCR-style receipt payload.
   - `data/external_charges.csv` – External fees such as ETC/charging records.

2. **Generate a claim form** using the built-in CLI (note the `PYTHONPATH=src` to pick up the package without installation):

   ```bash
   PYTHONPATH=src python -m expense_automation.main data/receipts_ocr.json data/external_charges.csv --output output/claim_form.csv
   ```

   The command writes a merged claim form to `output/claim_form.csv` with matching status, source notes, and a final reimbursable amount.

## How it works

- Parses OCR receipts and external CSV data.
- Matches rows by license plate and date.
- Prefers the external amount when a match exists; otherwise falls back to the receipt amount.
- 将未匹配到任何发票的外部交易单独追加到报表（标记为 `external_only`），避免遗漏支出。
- Exports a Tina Claim Form-style table (CSV) that Excel or WPS can open directly.

## Project layout

```
./data                      # Sample inputs for quick testing
./output                    # Generated claim forms (created on demand)
./src/expense_automation    # Core code: IO, matching, and CLI entrypoint
```

# Expense-Automation-Platform

An automated reimbursement generator that merges OCR-parsed receipt data with external sources (ETC, charging fees) to produce fully formatted reimbursement forms. The project now also ships a simple web UI so you can upload receipt images/Excel files and download a merged claim form directly.

## Getting started

1. **Inspect sample data** (already included):
   - `data/receipts_ocr.json` – OCR-style receipt payload.
   - `data/external_charges.csv` – External fees such as ETC/charging records.

2. **Generate a claim form via CLI** (note the `PYTHONPATH=src` to pick up the package without installation):

   ```bash
   PYTHONPATH=src python -m expense_automation.main data/receipts_ocr.json data/external_charges.csv --output output/claim_form.csv
   ```

   The command writes a merged claim form to `output/claim_form.csv` with matching status, source notes, and a final reimbursable amount.

3. **Start the web应用 (上传生成报销文件)**

   Install the optional web/Excel dependencies, then run the Flask app:

   ```bash
   pip install -r requirements.txt
   PYTHONPATH=src flask --app expense_automation.web_app run --host 0.0.0.0 --port 5000
   ```

   Open `http://localhost:5000` and上传：

   - 发票：JSON/CSV/Excel，或直接上传电子票据图片（图片将生成占位行，需后续补全金额）。
   - 外部交易：CSV/Excel（字段：plate, date, source, amount, note）。

   点击“生成报销 CSV”即可下载合并后的报销单。

## How it works

- Parses OCR receipts and external CSV/Excel data.
- Matches rows by license plate and date.
- Prefers the external amount when a match exists; otherwise falls back to the receipt amount.
- 将未匹配到任何发票的外部交易单独追加到报表（标记为 `external_only`），避免遗漏支出。
- 简易网页端：支持批量上传发票（含图片占位）与外部交易文件，直接下载报销 CSV。
- Exports a Tina Claim Form-style table (CSV) that Excel or WPS can open directly.

## Project layout

```
./data                      # Sample inputs for quick testing
./output                    # Generated claim forms (created on demand)
./src/expense_automation    # Core code: IO, matching, and CLI entrypoint
```

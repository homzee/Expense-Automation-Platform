# Expense-Automation-Platform

An automated reimbursement generator that merges OCR-parsed receipt data with external Excel sources (ETC, charging fees) to produce fully formatted reimbursement forms compliant with the “Tina Claim Form” standard. Built with a modular Python architecture supporting multi-source data fusion, validation, and precise Excel layout rendering.

For a deep-dive architecture evaluation and implementation roadmap, see [`docs/architecture_report.md`](docs/architecture_report.md).

## Quick start
1. Install dependencies (Python 3.10+ recommended):
   ```bash
   pip install -r requirements.txt
   ```
2. Place your blank claim template as `template.xlsx` in the project root.
3. Provide source files `source_etc.xlsx` and `source_charging.xlsx` (column names can be adjusted via `ExcelSourceReader`).
4. Run the pipeline demo:
   ```bash
   python main.py
   ```

The script prints item counts and generates `Final_Claim_Report.xlsx` when the template is available.

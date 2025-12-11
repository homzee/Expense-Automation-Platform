from __future__ import annotations

import io
import os
import tempfile
from pathlib import Path
from typing import List

from flask import Flask, flash, redirect, render_template_string, request, send_file, url_for
from werkzeug.utils import secure_filename

from .io_utils import load_external_charges, load_receipts, export_to_csv
from .processor import match_receipts_with_external


ALLOWED_RECEIPT_EXTS = {".json", ".csv", ".xlsx", ".xls", ".png", ".jpg", ".jpeg", ".webp"}
ALLOWED_EXTERNAL_EXTS = {".csv", ".xlsx", ".xls"}

app = Flask(__name__)
app.secret_key = os.environ.get("APP_SECRET_KEY", "dev-secret")


def _validate_file(filename: str, allowed_exts: set[str]) -> bool:
    return bool(filename) and Path(filename).suffix.lower() in allowed_exts


def _save_uploads(files: List, temp_dir: Path) -> List[Path]:
    saved_paths: List[Path] = []
    for upload in files:
        if not upload.filename:
            continue
        safe_name = secure_filename(upload.filename)
        target = temp_dir / safe_name
        upload.save(target)
        saved_paths.append(target)
    return saved_paths


@app.route("/", methods=["GET"])
def index() -> str:
    return render_template_string(INDEX_TEMPLATE)


@app.route("/generate", methods=["POST"])
def generate() -> str:
    receipt_files = request.files.getlist("receipts")
    external_file = request.files.get("external")

    if not receipt_files or not any(f.filename for f in receipt_files):
        flash("请上传至少一个发票文件（JSON/CSV/Excel/图片）。")
        return redirect(url_for("index"))

    if not external_file or not external_file.filename:
        flash("请上传外部交易文件（CSV/Excel）。")
        return redirect(url_for("index"))

    if not all(
        _validate_file(f.filename, ALLOWED_RECEIPT_EXTS) for f in receipt_files if f.filename
    ):
        flash("发票文件类型不支持，请使用 JSON、CSV、Excel 或常见图片格式。")
        return redirect(url_for("index"))

    if not _validate_file(external_file.filename, ALLOWED_EXTERNAL_EXTS):
        flash("外部交易文件类型不支持，请使用 CSV 或 Excel。")
        return redirect(url_for("index"))

    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        saved_receipts = _save_uploads(receipt_files, temp_dir)
        saved_external = _save_uploads([external_file], temp_dir)

        receipts_data = []
        for path in saved_receipts:
            receipts_data.extend(load_receipts(path))

        external_data = load_external_charges(saved_external[0])
        merged_rows = match_receipts_with_external(receipts_data, external_data)

        output_path = temp_dir / "claim_form.csv"
        export_to_csv(merged_rows, output_path)

        buffer = io.BytesIO(output_path.read_bytes())
        buffer.seek(0)
        return send_file(
            buffer,
            mimetype="text/csv",
            as_attachment=True,
            download_name="claim_form.csv",
        )


INDEX_TEMPLATE = """
<!doctype html>
<html lang="zh">
  <head>
    <meta charset="utf-8" />
    <title>报销生成器</title>
    <style>
      body { font-family: sans-serif; max-width: 840px; margin: 40px auto; line-height: 1.6; }
      form { border: 1px solid #ddd; padding: 20px; border-radius: 8px; }
      .field { margin-bottom: 12px; }
      .hint { color: #555; font-size: 0.95em; }
      .alert { color: #b30000; margin-bottom: 12px; }
      input[type="file"] { width: 100%; }
      button { padding: 10px 16px; background: #0366d6; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
      button:hover { background: #024f9c; }
    </style>
  </head>
  <body>
    <h1>上传凭证，自动生成报销文件</h1>
    <p>支持 OCR JSON/CSV/Excel 发票文件，或直接上传电子票据图片（将用占位信息快速生成）。外部交易支持 CSV/Excel。</p>

    {% with messages = get_flashed_messages() %}
      {% if messages %}
        {% for msg in messages %}
          <div class="alert">{{ msg }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}

    <form action="{{ url_for('generate') }}" method="post" enctype="multipart/form-data">
      <div class="field">
        <label for="receipts">发票文件（可多选）：</label><br />
        <input id="receipts" name="receipts" type="file" multiple accept=".json,.csv,.xlsx,.xls,.png,.jpg,.jpeg,.webp" required />
        <div class="hint">JSON/CSV/Excel 含字段：receipt_id, date, plate, merchant, amount, category；图片将生成占位数据，需后续补全金额。</div>
      </div>
      <div class="field">
        <label for="external">外部交易（CSV/Excel）：</label><br />
        <input id="external" name="external" type="file" accept=".csv,.xlsx,.xls" required />
        <div class="hint">字段：plate, date, source, amount, note</div>
      </div>
      <button type="submit">生成报销 CSV</button>
    </form>
  </body>
</html>
"""


def run() -> None:
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)


if __name__ == "__main__":
    run()

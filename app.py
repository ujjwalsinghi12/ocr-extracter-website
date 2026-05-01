import os
import tempfile

import ocrmypdf
import pandas as pd
from flask import Flask, render_template_string, request, send_file
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024


PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Document Converter Pro</title>
  <style>
    :root {
      color-scheme: light;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: #172033;
      background: #eef2f7;
    }
    body {
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 32px 16px;
    }
    main {
      width: min(960px, 100%);
      background: #ffffff;
      border: 1px solid #dbe3ef;
      border-radius: 8px;
      box-shadow: 0 18px 50px rgba(23, 32, 51, 0.12);
      overflow: hidden;
    }
    header {
      padding: 28px 32px;
      border-bottom: 1px solid #e6ecf5;
      background: #f8fafc;
    }
    h1 {
      margin: 0 0 8px;
      font-size: clamp(1.6rem, 4vw, 2.4rem);
      letter-spacing: 0;
    }
    p {
      margin: 0;
      color: #526173;
      line-height: 1.5;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 0;
    }
    section {
      padding: 32px;
    }
    section + section {
      border-left: 1px solid #e6ecf5;
    }
    h2 {
      margin: 0 0 10px;
      font-size: 1.15rem;
    }
    form {
      display: grid;
      gap: 16px;
      margin-top: 22px;
    }
    input[type="file"] {
      width: 100%;
      box-sizing: border-box;
      padding: 12px;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      background: #f8fafc;
    }
    button {
      min-height: 44px;
      border: 0;
      border-radius: 6px;
      background: #2563eb;
      color: white;
      font-weight: 700;
      cursor: pointer;
    }
    button:hover {
      background: #1d4ed8;
    }
    .message {
      padding: 14px 16px;
      border-top: 1px solid #e6ecf5;
      color: #9f1239;
      background: #fff1f2;
    }
    @media (max-width: 760px) {
      .grid {
        grid-template-columns: 1fr;
      }
      section + section {
        border-left: 0;
        border-top: 1px solid #e6ecf5;
      }
      header,
      section {
        padding: 24px;
      }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <h1>Document Converter Pro</h1>
      <p>Convert scanned PDFs into searchable PDFs, or export Excel sheets as CSV files.</p>
    </header>
    {% if message %}
      <div class="message">{{ message }}</div>
    {% endif %}
    <div class="grid">
      <section>
        <h2>PDF OCR Converter</h2>
        <p>Upload a PDF and download a searchable OCR-processed PDF.</p>
        <form action="/ocr" method="post" enctype="multipart/form-data">
          <input type="file" name="pdf_file" accept="application/pdf,.pdf" required>
          <button type="submit">Process PDF</button>
        </form>
      </section>
      <section>
        <h2>Excel to CSV Converter</h2>
        <p>Upload an Excel workbook and download the first sheet as a CSV file.</p>
        <form action="/excel" method="post" enctype="multipart/form-data">
          <input type="file" name="excel_file" accept=".xlsx,.xls" required>
          <button type="submit">Convert to CSV</button>
        </form>
      </section>
    </div>
  </main>
</body>
</html>
"""


def render_page(message=None):
    return render_template_string(PAGE, message=message)


@app.get("/")
def index():
    return render_page()


@app.post("/ocr")
def ocr_pdf():
    uploaded = request.files.get("pdf_file")
    if not uploaded or uploaded.filename == "":
        return render_page("Please upload a PDF file."), 400

    filename = secure_filename(uploaded.filename)
    if not filename.lower().endswith(".pdf"):
        return render_page("Please upload a valid PDF file."), 400

    input_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    output_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    input_file.close()
    output_file.close()

    try:
        uploaded.save(input_file.name)
        ocrmypdf.ocr(
            input_file.name,
            output_file.name,
            force_ocr=True,
            deskew=True,
            rotate_pages=True,
            oversample=300,
        )
        download_name = f"ocr_{filename}"
        return send_file(output_file.name, as_attachment=True, download_name=download_name)
    except Exception as exc:
        return render_page(f"OCR failed: {exc}"), 500
    finally:
        try:
            os.remove(input_file.name)
        except OSError:
            pass


@app.post("/excel")
def excel_to_csv():
    uploaded = request.files.get("excel_file")
    if not uploaded or uploaded.filename == "":
        return render_page("Please upload an Excel file."), 400

    filename = secure_filename(uploaded.filename)
    if not filename.lower().endswith((".xlsx", ".xls")):
        return render_page("Please upload a valid Excel file."), 400

    input_file = tempfile.NamedTemporaryFile(suffix=os.path.splitext(filename)[1], delete=False)
    output_file = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
    input_file.close()
    output_file.close()

    try:
        uploaded.save(input_file.name)
        df = pd.read_excel(
            input_file.name,
            engine="openpyxl",
            dtype=str,
            parse_dates=False,
            keep_default_na=False,
        )
        df.to_csv(output_file.name, index=False, encoding="utf-8")
        download_name = f"{os.path.splitext(filename)[0]}.csv"
        return send_file(output_file.name, as_attachment=True, download_name=download_name)
    except Exception as exc:
        return render_page(f"Conversion failed: {exc}"), 500
    finally:
        try:
            os.remove(input_file.name)
        except OSError:
            pass


if __name__ == "__main__":
    app.run(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "7860")),
    )

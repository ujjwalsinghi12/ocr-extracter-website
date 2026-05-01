import csv
import multiprocessing
import os
import tempfile

import ocrmypdf
import pandas as pd
from flask import Flask, after_this_request, render_template_string, request, send_file
from openpyxl import load_workbook
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
    input[type="file"],
    select {
      width: 100%;
      box-sizing: border-box;
      padding: 12px;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      background: #f8fafc;
      color: #172033;
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
    button:disabled {
      cursor: wait;
      background: #94a3b8;
    }
    .message {
      padding: 14px 16px;
      border-top: 1px solid #e6ecf5;
      color: #9f1239;
      background: #fff1f2;
    }
    .status {
      min-height: 22px;
      color: #2563eb;
      font-weight: 650;
    }
    .status.error {
      color: #9f1239;
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
        <form action="/ocr" method="post" enctype="multipart/form-data" data-download-form>
          <input type="file" name="pdf_file" accept="application/pdf,.pdf" required>
          <select name="mode" aria-label="OCR mode">
            <option value="fast" selected>Fast OCR - skip pages that already have text</option>
            <option value="accurate">High accuracy - slower full OCR</option>
          </select>
          <button type="submit">Process PDF</button>
          <div class="status" aria-live="polite"></div>
        </form>
      </section>
      <section>
        <h2>Excel to CSV Converter</h2>
        <p>Upload an Excel workbook and download the first sheet as a CSV file.</p>
        <form action="/excel" method="post" enctype="multipart/form-data" data-download-form>
          <input type="file" name="excel_file" accept=".xlsx,.xls" required>
          <button type="submit">Convert to CSV</button>
          <div class="status" aria-live="polite"></div>
        </form>
      </section>
    </div>
  </main>
  <script>
    function filenameFromDisposition(disposition, fallback) {
      if (!disposition) return fallback;
      const match = disposition.match(/filename="?([^"]+)"?/i);
      return match ? match[1] : fallback;
    }

    document.querySelectorAll("[data-download-form]").forEach((form) => {
      form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const button = form.querySelector("button");
        const status = form.querySelector(".status");
        const originalText = button.textContent;
        const fallbackName = form.action.endsWith("/excel") ? "converted.csv" : "processed.pdf";

        button.disabled = true;
        button.textContent = "Processing...";
        status.classList.remove("error");
        status.textContent = form.action.endsWith("/ocr")
          ? "Uploading and processing. Fast mode skips pages that already contain text."
          : "Uploading and converting. Large workbooks may take a moment.";

        try {
          const response = await fetch(form.action, {
            method: "POST",
            body: new FormData(form),
          });

          if (!response.ok) {
            const message = await response.text();
            throw new Error(message.replace(/<[^>]*>/g, " ").replace(/\\s+/g, " ").trim() || "Processing failed.");
          }

          const blob = await response.blob();
          const url = URL.createObjectURL(blob);
          const link = document.createElement("a");
          link.href = url;
          link.download = filenameFromDisposition(response.headers.get("content-disposition"), fallbackName);
          document.body.appendChild(link);
          link.click();
          link.remove();
          URL.revokeObjectURL(url);

          status.textContent = "Done. Your download should start automatically.";
          form.reset();
        } catch (error) {
          status.classList.add("error");
          status.textContent = error.message || "Processing failed.";
        } finally {
          button.disabled = false;
          button.textContent = originalText;
        }
      });
    });
  </script>
</body>
</html>
"""


def render_page(message=None):
    return render_template_string(PAGE, message=message)


@app.get("/")
def index():
    return render_page()


@app.get("/health")
def health():
    return {"status": "ok"}


def remove_later(path):
    def cleanup():
        try:
            os.remove(path)
        except OSError:
            pass

    @after_this_request
    def schedule_cleanup(response):
        response.call_on_close(cleanup)
        return response


def ocr_options(mode):
    workers = max(1, min(4, multiprocessing.cpu_count()))
    if mode == "accurate":
        return {
            "force_ocr": True,
            "deskew": True,
            "rotate_pages": True,
            "oversample": 300,
            "optimize": 1,
            "jobs": workers,
            "progress_bar": False,
        }

    return {
        "skip_text": True,
        "deskew": False,
        "rotate_pages": False,
        "oversample": 150,
        "optimize": 1,
        "jobs": workers,
        "progress_bar": False,
    }


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
        os.remove(output_file.name)
        ocrmypdf.ocr(
            input_file.name,
            output_file.name,
            **ocr_options(request.form.get("mode", "fast")),
        )
        download_name = f"ocr_{filename}"
        remove_later(output_file.name)
        return send_file(output_file.name, as_attachment=True, download_name=download_name)
    except Exception as exc:
        return render_page(f"OCR failed: {exc}"), 500
    finally:
        try:
            os.remove(input_file.name)
        except OSError:
            pass


def convert_xlsx_to_csv(input_path, output_path):
    workbook = load_workbook(input_path, read_only=True, data_only=True)
    try:
        sheet = workbook.active
        with open(output_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            for row in sheet.iter_rows(values_only=True):
                writer.writerow(["" if value is None else value for value in row])
    finally:
        workbook.close()


def convert_excel_file(input_path, output_path, extension):
    if extension == ".xlsx":
        convert_xlsx_to_csv(input_path, output_path)
        return

    df = pd.read_excel(
        input_path,
        dtype=str,
        parse_dates=False,
        keep_default_na=False,
    )
    df.to_csv(output_path, index=False, encoding="utf-8")


@app.post("/excel")
def excel_to_csv():
    uploaded = request.files.get("excel_file")
    if not uploaded or uploaded.filename == "":
        return render_page("Please upload an Excel file."), 400

    filename = secure_filename(uploaded.filename)
    if not filename.lower().endswith((".xlsx", ".xls")):
        return render_page("Please upload a valid Excel file."), 400

    extension = os.path.splitext(filename)[1].lower()
    input_file = tempfile.NamedTemporaryFile(suffix=extension, delete=False)
    output_file = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
    input_file.close()
    output_file.close()

    try:
        uploaded.save(input_file.name)
        convert_excel_file(input_file.name, output_file.name, extension)
        download_name = f"{os.path.splitext(filename)[0]}.csv"
        remove_later(output_file.name)
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

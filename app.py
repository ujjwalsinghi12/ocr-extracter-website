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
      background: #e8edf5;
    }
    * {
      box-sizing: border-box;
    }
    body {
      margin: 0;
      min-height: 100vh;
      padding: 28px 18px;
      background:
        radial-gradient(circle at top left, rgba(37, 99, 235, 0.16), transparent 30rem),
        linear-gradient(135deg, #f8fafc 0%, #e8edf5 52%, #e6f4ef 100%);
    }
    main {
      width: min(1120px, 100%);
      margin: 0 auto;
    }
    header {
      display: grid;
      gap: 18px;
      padding: 34px 0 26px;
    }
    h1 {
      margin: 0 0 8px;
      font-size: clamp(2rem, 5vw, 4rem);
      line-height: 1;
      letter-spacing: 0;
      color: #0f172a;
    }
    p {
      margin: 0;
      color: #526173;
      line-height: 1.5;
    }
    .hero-copy {
      max-width: 740px;
    }
    .hero-copy p {
      font-size: 1.03rem;
    }
    .toolbar {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }
    .pill {
      display: inline-flex;
      align-items: center;
      min-height: 32px;
      padding: 6px 10px;
      border-radius: 999px;
      border: 1px solid rgba(37, 99, 235, 0.18);
      background: rgba(255, 255, 255, 0.72);
      color: #1f3f75;
      font-size: 0.88rem;
      font-weight: 700;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 18px;
    }
    section {
      display: grid;
      align-content: start;
      gap: 18px;
      min-height: 440px;
      padding: 26px;
      background: rgba(255, 255, 255, 0.86);
      border: 1px solid rgba(148, 163, 184, 0.32);
      border-radius: 8px;
      box-shadow: 0 20px 55px rgba(15, 23, 42, 0.12);
      backdrop-filter: blur(12px);
    }
    .panel-top {
      display: grid;
      gap: 10px;
    }
    h2 {
      margin: 0;
      font-size: 1.35rem;
      color: #111827;
    }
    .tag {
      width: fit-content;
      padding: 6px 9px;
      border-radius: 6px;
      background: #ecfdf5;
      color: #047857;
      font-size: 0.78rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    form {
      display: grid;
      gap: 16px;
      margin-top: 4px;
    }
    input[type="file"],
    select {
      width: 100%;
      min-height: 48px;
      padding: 12px 14px;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      background: #ffffff;
      color: #172033;
      font: inherit;
    }
    input[type="file"]::file-selector-button {
      margin-right: 12px;
      border: 0;
      border-radius: 5px;
      background: #e0f2fe;
      color: #075985;
      padding: 9px 12px;
      font-weight: 800;
    }
    button {
      min-height: 44px;
      border: 0;
      border-radius: 6px;
      background: linear-gradient(135deg, #2563eb, #059669);
      color: white;
      font-weight: 700;
      cursor: pointer;
      font: inherit;
      box-shadow: 0 10px 22px rgba(37, 99, 235, 0.22);
    }
    button:hover {
      filter: brightness(0.96);
    }
    button:disabled {
      cursor: wait;
      background: #94a3b8;
      box-shadow: none;
    }
    .message {
      padding: 14px 16px;
      margin-bottom: 18px;
      border: 1px solid #fecdd3;
      border-radius: 8px;
      color: #9f1239;
      background: #fff1f2;
    }
    .progress-wrap {
      display: none;
      gap: 8px;
    }
    .progress-wrap.active {
      display: grid;
    }
    .progress-label {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      color: #334155;
      font-size: 0.9rem;
      font-weight: 750;
    }
    .progress-track {
      height: 10px;
      overflow: hidden;
      border-radius: 999px;
      background: #dbe5f1;
    }
    .progress-bar {
      width: 0%;
      height: 100%;
      border-radius: inherit;
      background: linear-gradient(90deg, #2563eb, #22c55e, #f59e0b);
      transition: width 320ms ease;
    }
    .status {
      min-height: 24px;
      color: #2563eb;
      font-weight: 650;
    }
    .status.success {
      color: #047857;
    }
    .status.error {
      color: #9f1239;
    }
    .download-link {
      display: none;
      align-items: center;
      justify-content: center;
      min-height: 44px;
      border-radius: 6px;
      background: #111827;
      color: #ffffff;
      text-decoration: none;
      font-weight: 800;
    }
    .download-link.ready {
      display: flex;
    }
    .details {
      display: grid;
      gap: 8px;
      margin-top: auto;
      padding-top: 8px;
      color: #64748b;
      font-size: 0.9rem;
    }
    @media (max-width: 760px) {
      body {
        padding: 18px 12px;
      }
      .grid {
        grid-template-columns: 1fr;
      }
      section {
        min-height: auto;
        padding: 22px;
      }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <div class="hero-copy">
        <h1>Document Converter Pro</h1>
        <p>Fast OCR and spreadsheet conversion in one focused workspace. Upload your file, watch the process complete, then download only when the processed document is ready.</p>
      </div>
      <div class="toolbar" aria-label="Capabilities">
        <span class="pill">PDF OCR</span>
        <span class="pill">Excel to CSV</span>
        <span class="pill">Fast mode</span>
        <span class="pill">Private processing</span>
      </div>
    </header>
    {% if message %}
      <div class="message">{{ message }}</div>
    {% endif %}
    <div class="grid">
      <section>
        <div class="panel-top">
          <span class="tag">OCR engine</span>
          <h2>PDF OCR Converter</h2>
          <p>Turn scanned PDFs into searchable documents. Fast mode skips pages that already contain selectable text.</p>
        </div>
        <form action="/ocr" method="post" enctype="multipart/form-data" data-download-form>
          <input type="file" name="pdf_file" accept="application/pdf,.pdf" required>
          <select name="mode" aria-label="OCR mode">
            <option value="fast" selected>Fast OCR - skip pages that already have text</option>
            <option value="accurate">High accuracy - slower full OCR</option>
          </select>
          <button type="submit">Process PDF</button>
          <div class="progress-wrap" aria-hidden="true">
            <div class="progress-label">
              <span>Processing document</span>
              <span data-progress-value>0%</span>
            </div>
            <div class="progress-track">
              <div class="progress-bar"></div>
            </div>
          </div>
          <div class="status" aria-live="polite"></div>
          <a class="download-link" href="#" download>Download processed document</a>
        </form>
        <div class="details">
          <span>Best for: scanned PDFs, contracts, reports, office paperwork.</span>
          <span>Tip: use high accuracy only when fast mode misses text.</span>
        </div>
      </section>
      <section>
        <div class="panel-top">
          <span class="tag">Spreadsheet export</span>
          <h2>Excel to CSV Converter</h2>
          <p>Convert the first worksheet into a clean CSV file using a memory-efficient streaming path for XLSX workbooks.</p>
        </div>
        <form action="/excel" method="post" enctype="multipart/form-data" data-download-form>
          <input type="file" name="excel_file" accept=".xlsx,.xls" required>
          <button type="submit">Convert to CSV</button>
          <div class="progress-wrap" aria-hidden="true">
            <div class="progress-label">
              <span>Processing document</span>
              <span data-progress-value>0%</span>
            </div>
            <div class="progress-track">
              <div class="progress-bar"></div>
            </div>
          </div>
          <div class="status" aria-live="polite"></div>
          <a class="download-link" href="#" download>Download processed document</a>
        </form>
        <div class="details">
          <span>Best for: tables, exports, lead lists, accounting sheets.</span>
          <span>Output: first worksheet saved as UTF-8 CSV.</span>
        </div>
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
      let activeDownloadUrl = null;

      form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const button = form.querySelector("button");
        const status = form.querySelector(".status");
        const progressWrap = form.querySelector(".progress-wrap");
        const progressBar = form.querySelector(".progress-bar");
        const progressValue = form.querySelector("[data-progress-value]");
        const downloadLink = form.querySelector(".download-link");
        const originalText = button.textContent;
        const fallbackName = form.action.endsWith("/excel") ? "converted.csv" : "processed.pdf";
        let progress = 0;
        let progressTimer = null;

        if (activeDownloadUrl) {
          URL.revokeObjectURL(activeDownloadUrl);
          activeDownloadUrl = null;
        }
        downloadLink.classList.remove("ready");
        downloadLink.removeAttribute("href");

        const setProgress = (value) => {
          progress = Math.max(progress, Math.min(value, 100));
          progressBar.style.width = `${progress}%`;
          progressValue.textContent = `${Math.round(progress)}%`;
        };

        button.disabled = true;
        button.textContent = "Processing...";
        progressWrap.classList.add("active");
        progressWrap.setAttribute("aria-hidden", "false");
        setProgress(8);
        status.classList.remove("error", "success");
        status.textContent = form.action.endsWith("/ocr")
          ? "Uploading and processing. Fast mode skips pages that already contain text."
          : "Uploading and converting. Large workbooks may take a moment.";

        try {
          progressTimer = window.setInterval(() => {
            const next = progress < 55 ? progress + 7 : progress < 86 ? progress + 3 : progress + 0.6;
            setProgress(Math.min(next, 94));
          }, 650);

          const response = await fetch(form.action, {
            method: "POST",
            body: new FormData(form),
          });

          if (!response.ok) {
            const message = await response.text();
            throw new Error(message.replace(/<[^>]*>/g, " ").replace(/\\s+/g, " ").trim() || "Processing failed.");
          }

          const blob = await response.blob();
          activeDownloadUrl = URL.createObjectURL(blob);
          downloadLink.href = activeDownloadUrl;
          downloadLink.download = filenameFromDisposition(response.headers.get("content-disposition"), fallbackName);
          downloadLink.classList.add("ready");

          setProgress(100);
          status.classList.add("success");
          status.textContent = "Processed. Your document is ready to download.";
        } catch (error) {
          setProgress(100);
          status.classList.add("error");
          status.textContent = error.message || "Processing failed.";
        } finally {
          if (progressTimer) {
            window.clearInterval(progressTimer);
          }
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

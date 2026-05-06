---
title: SCANLY
emoji: 📄
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
---

# SCANLY

SCANLY is a Flask web app for:

- PDF OCR conversion with `ocrmypdf`
- Excel to CSV conversion with `pandas` and `openpyxl`
- PDF to Word conversion
- PDF splitting
- PDF page deletion
- PDF text summary
- Fast default OCR mode that skips pages that already contain text
- Streaming `.xlsx` conversion to reduce memory use on large workbooks
- Razorpay payment before paid processing

## Important: GitHub Pages will not run this app

This project uses Python and system OCR tools, so it cannot be hosted directly on GitHub Pages. GitHub Pages only serves static HTML/CSS/JavaScript.

Use GitHub as the source repository, then deploy the app to a Python/container host such as Hugging Face Spaces, Render, Fly.io, Railway, or any Docker-capable server.

## Deploy from GitHub to Hugging Face Spaces

1. Push this folder to a GitHub repository.
2. Create a Hugging Face Space.
3. Select **Docker** as the Space SDK.
4. In your GitHub repository settings, add:
   - Repository secret `HF_TOKEN`: a Hugging Face access token with write access
   - Repository variable `HF_SPACE`: your Space id, for example `yourname/document-converter-pro`
5. Push to the `main` branch, or run the **Deploy to Hugging Face Space** workflow manually from the GitHub Actions tab.

The included `Dockerfile` installs the required OCR system packages and starts `app.py` on port `7860`.

## Razorpay setup

PDF and paid Excel processing is payment gated. The app counts PDF pages or Excel rows, creates a Razorpay order when the file exceeds the free tier, waits for a successful Checkout payment, verifies the payment signature on the server, and only then starts processing.

Set these environment variables in your deployment host or Hugging Face Space secrets:

```bash
RAZORPAY_KEY_ID=rzp_test_or_live_key_id
RAZORPAY_KEY_SECRET=your_key_secret
```

OCR pricing is configured in `app.py` as `OCR_PRICE_PER_PAGE_PAISE = 500`, which is INR 5.00 per page.

Other PDF tools use `PDF_FREE_PAGES = 10` and `PDF_EXTRA_PAGE_PRICE_PAISE = 200`, which means the first 10 pages are free and additional pages cost INR 2.00 per page.

Excel to CSV uses `EXCEL_FREE_ROWS = 500`, `EXCEL_PRICE_PER_EXTRA_ROW_PAISE = 20`, and `EXCEL_MAX_ROWS = 50000`, which means the first 500 rows are free, additional rows cost INR 0.20 per row, and files above 50,000 rows are rejected.

The owner bypass key defaults to `215836`. To change it without editing code, set this optional secret:

```bash
OCR_BYPASS_KEY=your_private_access_key
```

## Run locally

Install system dependencies first:

- `ocrmypdf`
- `tesseract-ocr`
- `poppler-utils`
- `ghostscript`
- `qpdf`

Then run:

```bash
pip install -r requirements.txt
python app.py
```

Open `http://localhost:7860`.

## Files

- `app.py`: deployable Flask app
- `Dockerfile`: container build for deployment
- `requirements.txt`: Python dependencies
- `.github/workflows/deploy-huggingface.yml`: optional GitHub Actions deployment workflow

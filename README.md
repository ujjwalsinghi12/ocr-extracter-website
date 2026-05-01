# Document Converter Pro

Document Converter Pro is a Gradio web app for:

- PDF OCR conversion with `ocrmypdf`
- Excel to CSV conversion with `pandas` and `openpyxl`

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

- `app.py`: deployable Gradio app
- `Dockerfile`: container build for deployment
- `requirements.txt`: Python dependencies
- `.github/workflows/deploy-huggingface.yml`: optional GitHub Actions deployment workflow

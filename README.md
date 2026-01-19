# Document Converter Pro

A powerful document conversion tool that combines PDF OCR conversion and Excel to CSV conversion in a single interface.

## Features

- **PDF OCR Conversion**: Convert scanned PDFs to searchable, text-based PDFs using ocrmypdf
- **Excel to CSV Conversion**: Convert Excel files to CSV format quickly and efficiently
- **Web Interface**: Built with Gradio for an intuitive user experience
- **Optimized Processing**: Fast conversion with optimized parameters

## Deployment to Hugging Face Spaces

This application is ready to be deployed on Hugging Face Spaces as a free, public application.

### Steps to Deploy:

1. **Sign up on Hugging Face**
   - Go to [huggingface.co](https://huggingface.co) and create an account

2. **Create a New Space**
   - Click on your profile icon → "New Space"
   - Fill in the details:
     - Name: Choose a unique name for your application
     - License: Select appropriate license
     - SDK: Select "Docker" (required for ocrmypdf)
     - Visibility: Public or Private

3. **Configure the Space**
   - Use the files provided in this repository:
     - `app.py` - Main application file
     - `requirements.txt` - Python dependencies
     - `Dockerfile` - Container configuration (see below)

4. **Create a Dockerfile** (needed for ocrmypdf dependencies)
   ```Dockerfile
   FROM huggingface/transformers-all-deepspeed:latest
   
   RUN apt-get update && apt-get install -y \
       ocrmypdf \
       tesseract-ocr \
       poppler-utils \
       && rm -rf /var/lib/apt/lists/*
   
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   
   COPY . .
   
   CMD ["python", "app.py"]
   ```

5. **Alternative Dockerfile** (lighter image)
   ```Dockerfile
   FROM python:3.10-slim
   
   # Install system dependencies
   RUN apt-get update && apt-get install -y \
       ocrmypdf \
       tesseract-ocr \
       poppler-utils \
       gcc \
       && rm -rf /var/lib/apt/lists/*
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   
   COPY . .
   
   EXPOSE 7860
   
   CMD ["python", "app.py"]
   ```

6. **Upload Files**
   - Upload all files to your Space repository
   - Or connect your GitHub repository for automatic synchronization

7. **Wait for Build**
   - Hugging Face will automatically build and deploy your application
   - This may take several minutes due to the size of OCR dependencies

## How to Use

### PDF OCR Conversion:
1. Navigate to the "PDF OCR Converter" tab
2. Upload your PDF file
3. Click "Process PDF with OCR"
4. Wait for processing to complete
5. Download the OCRed PDF when finished

### Excel to CSV Conversion:
1. Navigate to the "Excel to CSV Converter" tab
2. Upload your Excel file (.xlsx or .xls)
3. Click "Convert to CSV"
4. Download the converted CSV file when finished

## Technical Details

The application uses:
- **ocrmypdf**: For PDF OCR processing with parameters: `--force-ocr --deskew --rotate-pages --oversample 300`
- **pandas**: For fast Excel to CSV conversion with optimized settings
- **Gradio**: For the user interface
- **openpyxl**: For Excel file processing

## Requirements

- Python 3.8+
- System dependencies: ocrmypdf, tesseract-ocr, poppler-utils

## Local Development

To run locally:
```bash
pip install -r requirements.txt
python app.py
```

Then visit `http://localhost:7860` in your browser.
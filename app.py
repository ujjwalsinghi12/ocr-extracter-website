import gradio as gr
import ocrmypdf
import pandas as pd
import openpyxl
import tempfile
import os
import uuid
from werkzeug.utils import secure_filename

def ocr_pdf(input_pdf):
    """Process PDF with OCR using ocrmypdf"""
    if input_pdf is None:
        return None, "Please upload a PDF file"
    
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_output:
        try:
            # Process with ocrmypdf using the parameters you specified
            ocrmypdf.ocr(
                input_pdf.name, 
                temp_output.name, 
                force_ocr=True,
                deskew=True, 
                rotate_pages=True, 
                oversample=300
            )
            return temp_output.name, "PDF processed successfully!"
        except Exception as e:
            return None, f"Error processing PDF: {str(e)}"

def convert_excel_to_csv(input_excel):
    """Convert Excel file to CSV"""
    if input_excel is None:
        return None, "Please upload an Excel file"
    
    try:
        # Read Excel file with optimizations for speed
        df = pd.read_excel(
            input_excel.name,
            engine="openpyxl",
            dtype=str,          # Big speed boost
            parse_dates=False,  # No date parsing
            keep_default_na=False
        )
        
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='', encoding='utf-8') as temp_csv:
            df.to_csv(temp_csv.name, index=False, encoding="utf-8")
            return temp_csv.name, "Excel converted to CSV successfully!"
    except Exception as e:
        return None, f"Error converting Excel: {str(e)}"

# Create Gradio interface with tabs
with gr.Blocks(title="Document Converter Pro", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 📄 Document Converter Pro")
    gr.Markdown("Convert your documents with ease using our powerful online tools")
    
    with gr.Tabs():
        with gr.TabItem("PDF OCR Converter"):
            gr.Markdown("### Convert scanned PDFs to searchable, text-based PDFs")
            with gr.Row():
                with gr.Column():
                    pdf_input = gr.File(label="Upload PDF", file_types=[".pdf"])
                    pdf_btn = gr.Button("Process PDF with OCR")
                with gr.Column():
                    pdf_output = gr.File(label="Download OCRed PDF")
                    pdf_status = gr.Textbox(label="Status", interactive=False)
            
            pdf_btn.click(
                fn=ocr_pdf,
                inputs=pdf_input,
                outputs=[pdf_output, pdf_status]
            )
        
        with gr.TabItem("Excel to CSV Converter"):
            gr.Markdown("### Convert Excel files to CSV format quickly and efficiently")
            with gr.Row():
                with gr.Column():
                    excel_input = gr.File(label="Upload Excel", file_types=[".xlsx", ".xls"])
                    excel_btn = gr.Button("Convert to CSV")
                with gr.Column():
                    excel_output = gr.File(label="Download CSV")
                    excel_status = gr.Textbox(label="Status", interactive=False)
            
            excel_btn.click(
                fn=convert_excel_to_csv,
                inputs=excel_input,
                outputs=[excel_output, excel_status]
            )

if __name__ == "__main__":
    demo.launch(server_port=int(os.getenv("PORT", 7860)))
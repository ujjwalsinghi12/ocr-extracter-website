from flask import Flask, render_template, request, send_file, redirect, url_for, flash, jsonify
import os
import subprocess
import tempfile
import uuid
from werkzeug.utils import secure_filename
import threading
import time

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Import for Excel processing
import pandas as pd
import openpyxl

# Configuration
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# Global dictionary to store processing status
processing_status = {}

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_pdf_file(file_path):
    """Validate that the uploaded file is actually a PDF"""
    try:
        # Check if file exists and has PDF header
        if not os.path.exists(file_path):
            return False, "File does not exist"
            
        # Read first few bytes to check PDF header
        with open(file_path, 'rb') as f:
            header = f.read(4)
            if header != b'%PDF':
                return False, "File is not a valid PDF"
                
        # Check file size (max 50MB)
        file_size = os.path.getsize(file_path)
        max_size = 50 * 1024 * 1024  # 50MB
        if file_size > max_size:
            return False, f"File size too large. Max size is 50MB, got {file_size / (1024*1024):.1f}MB"
            
        return True, "Valid PDF"
    except Exception as e:
        return False, f"Error validating PDF: {str(e)}"

def process_pdf_with_ocr(input_path, output_path, job_id=None):
    """Process PDF with OCR using ocrmypdf"""
    try:
        # Using the ocrmypdf command similar to what was provided
        cmd = [
            'ocrmypdf',
            '--force-ocr',
            '--deskew',
            '--rotate-pages',
            '--oversample', '300',
            input_path,
            output_path
        ]
        
        import logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        
        logger.info(f"Executing OCR command: {' '.join(cmd)}")
        
        # Run the command and capture output in real-time
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        logger.info(f"OCR process completed with return code: {result.returncode}")
        if result.stdout:
            logger.info(f"OCR stdout: {result.stdout}")
        if result.stderr:
            logger.info(f"OCR stderr: {result.stderr}")
        
        if result.returncode != 0:
            raise Exception(f"OCR processing failed with return code {result.returncode}: {result.stderr}")
            
        return True
    except subprocess.TimeoutExpired:
        raise Exception("Processing timed out after 10 minutes")
    except Exception as e:
        import logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        logger.error(f"OCR processing error: {str(e)}")
        raise e

# Main routes
@app.route('/')
def index():
    """Main page route"""
    return render_template('index.html')

@app.route('/pdf-ocr')
def pdf_ocr():
    """PDF OCR converter page route"""
    return render_template('pdf_ocr.html')

@app.route('/excel-to-csv')
def excel_to_csv():
    """Excel to CSV converter page route"""
    return render_template('excel_to_csv.html')

# Routes for PDF OCR functionality
@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle PDF file upload"""
    if 'pdf_file' not in request.files:
        return jsonify({'success': False, 'message': 'No file selected'})
    
    file = request.files['pdf_file']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        # Validate the PDF file
        is_valid, validation_msg = validate_pdf_file(filepath)
        if not is_valid:
            # Clean up invalid file
            try:
                os.remove(filepath)
            except:
                pass  # Ignore cleanup errors
            return jsonify({'success': False, 'message': f'Invalid PDF file: {validation_msg}'})
        
        # Generate unique output filename
        output_filename = f"ocr_{unique_filename}"
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
        
        # Store processing status
        job_id = str(uuid.uuid4())
        processing_status[job_id] = {
            'status': 'processing',
            'input_file': filepath,
            'output_file': output_path,
            'progress': 0
        }
        
        # Start processing in a separate thread
        thread = threading.Thread(target=process_file_thread, args=(job_id,))
        thread.start()
        
        return jsonify({
            'success': True, 
            'job_id': job_id,
            'message': 'File uploaded successfully. Processing started...'
        })
    else:
        return jsonify({'success': False, 'message': 'Invalid file type. Please upload a PDF.'})

def process_file_thread(job_id):
    """Process file in a separate thread"""
    status = processing_status.get(job_id)
    if not status:
        return
        
    try:
        # Update progress
        processing_status[job_id]['progress'] = 5
        time.sleep(0.5)  # Brief pause
        
        # Estimate progress based on file size
        input_size = os.path.getsize(status['input_file'])
        estimated_pages = max(1, input_size // (100 * 1024))  # Rough estimate: 1 page per 100KB
        
        # Update progress incrementally
        base_progress = 5
        progress_increment = (90 - base_progress) / estimated_pages  # 90% total for processing
        
        for page in range(estimated_pages):
            # In a real implementation, we would track actual OCR progress
            # Here we simulate progress based on estimated pages
            simulated_progress = int(base_progress + (page * progress_increment))
            processing_status[job_id]['progress'] = min(simulated_progress, 95)
            time.sleep(0.1)  # Small delay to simulate processing time per page
        
        # Perform OCR processing
        process_pdf_with_ocr(status['input_file'], status['output_file'], job_id)
        
        # Update status when complete
        processing_status[job_id]['status'] = 'completed'
        processing_status[job_id]['progress'] = 100
    except Exception as e:
        processing_status[job_id]['status'] = 'failed'
        processing_status[job_id]['error'] = str(e)
        processing_status[job_id]['progress'] = 0
        
        # Clean up failed output file if it exists
        try:
            if os.path.exists(status['output_file']):
                os.remove(status['output_file'])
        except:
            pass  # Ignore cleanup errors

@app.route('/status/<job_id>')
def get_status(job_id):
    """Get processing status for a job"""
    if job_id in processing_status:
        return jsonify(processing_status[job_id])
    else:
        return jsonify({'status': 'not_found'})

@app.route('/download/<job_id>')
def download_file(job_id):
    """Download processed file"""
    if job_id in processing_status:
        status = processing_status[job_id]
        if status['status'] == 'completed':
            return send_file(status['output_file'], as_attachment=True, 
                           download_name=f"ocr_processed_{os.path.basename(status['output_file'])}")
        else:
            flash('File is not ready for download')
            return redirect(url_for('index'))
    else:
        flash('Invalid job ID')
        return redirect(url_for('index'))

@app.route('/cleanup', methods=['POST'])
def cleanup():
    """Clean up temporary files"""
    # Clean up uploaded files older than 1 hour
    current_time = time.time()
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.isfile(file_path):
            if current_time - os.path.getmtime(file_path) > 3600:  # 1 hour
                os.remove(file_path)
    
    # Clean up processed files older than 1 hour
    for filename in os.listdir(app.config['PROCESSED_FOLDER']):
        file_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
        if os.path.isfile(file_path):
            if current_time - os.path.getmtime(file_path) > 3600:  # 1 hour
                os.remove(file_path)
    
    # Clean up old processing statuses
    expired_jobs = []
    for job_id, status in processing_status.items():
        if status['status'] == 'completed' and current_time - os.path.getmtime(status['output_file']) > 3600:
            expired_jobs.append(job_id)
    
    for job_id in expired_jobs:
        del processing_status[job_id]
    
    return jsonify({'success': True, 'message': 'Cleanup completed'})


# Routes for Excel to CSV functionality
@app.route('/convert-excel', methods=['POST'])
def convert_excel_to_csv():
    """Convert Excel files to CSV"""
    try:
        if 'excel_file' not in request.files:
            return jsonify({'success': False, 'message': 'No file selected'})
        
        file = request.files['excel_file']
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'})
        
        if file and file.filename.lower().endswith(('.xlsx', '.xls')):
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)
            
            # Convert Excel to CSV
            output_filename = f"{os.path.splitext(unique_filename)[0]}.csv"
            output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
            
            # Process Excel file to CSV
            df = pd.read_excel(
                filepath,
                engine="openpyxl",
                dtype=str,
                parse_dates=False,
                keep_default_na=False
            )
            
            df.to_csv(output_path, index=False, encoding="utf-8")
            
            # Clean up uploaded file
            try:
                os.remove(filepath)
            except:
                pass  # Ignore cleanup errors
            
            return jsonify({
                'success': True,
                'output_filename': output_filename,
                'message': 'File converted successfully!'
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid file type. Please upload an Excel file (.xlsx or .xls)'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Conversion failed: {str(e)}'})

@app.route('/download-csv/<filename>')
def download_csv(filename):
    """Download converted CSV file"""
    try:
        file_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True, 
                           download_name=f"converted_{filename}")
        else:
            flash('File not found')
            return redirect(url_for('excel_to_csv'))
    except Exception as e:
        flash(f'Download failed: {str(e)}')
        return redirect(url_for('excel_to_csv'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
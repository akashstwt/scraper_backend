"""
Flask API Backend for Price Scraper Web Application
Handles file uploads, scraping jobs, and email notifications
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import uuid
import threading
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import sys

# Add parent directory to import scraper modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'price_scrapper'))

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# Job status storage (in production, use Redis or database)
jobs = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def worker_process(args):
    """Worker function for parallel processing - must be at module level for pickling"""
    worker_id, oem_codes_chunk, use_selenium, job_id = args
    results = []
    
    # Import inside worker to avoid pickling issues
    from scrapers.hottoner_scraper import scrape_hottoner
    from scrapers.selenium_scraper import SeleniumScraper
    
    selenium_scraper = None
    if use_selenium:
        selenium_scraper = SeleniumScraper(headless=False)
    
    try:
        for i, code in enumerate(oem_codes_chunk, 1):
            row_data = {"OEM_CODE": code}
            
            # Scrape InkStation with Selenium
            if use_selenium and selenium_scraper:
                try:
                    result = selenium_scraper.scrape_inkstation(code)
                    if result:
                        row_data["Ink Station"] = result.get("Price", "N/A")
                    else:
                        row_data["Ink Station"] = "N/A"
                except Exception as e:
                    row_data["Ink Station"] = "Error"
            
            # Scrape HotToner
            try:
                result = scrape_hottoner(code)
                if result:
                    row_data["Hot Tonner"] = result.get("Price", "N/A")
                else:
                    row_data["Hot Tonner"] = "N/A"
            except Exception as e:
                row_data["Hot Tonner"] = "Error"
            
            results.append(row_data)
            
            # Update progress (thread-safe update)
            if job_id in jobs:
                jobs[job_id]['progress']['current'] += 1
    
    finally:
        if selenium_scraper:
            selenium_scraper.close()
    
    return results


def run_scraper_job(job_id, input_file, output_file, email):
    """Run the scraper in a background thread"""
    try:
        # Import scraper modules
        from utils.excel_handler import read_oem_codes
        import pandas as pd
        from multiprocessing import Pool
        
        jobs[job_id]['status'] = 'running'
        jobs[job_id]['message'] = 'Reading OEM codes from file...'
        
        # Read OEM codes
        oem_codes = read_oem_codes(input_file)
        total_codes = len(oem_codes)
        
        jobs[job_id]['progress'] = {'current': 0, 'total': total_codes}
        jobs[job_id]['message'] = f'Found {total_codes} OEM codes. Starting parallel scraping...'
        
        # Split codes into chunks for parallel processing
        num_workers = 4
        chunk_size = len(oem_codes) // num_workers
        chunks = []
        for i in range(num_workers):
            start_idx = i * chunk_size
            if i == num_workers - 1:
                end_idx = len(oem_codes)
            else:
                end_idx = start_idx + chunk_size
            chunks.append(oem_codes[start_idx:end_idx])
        
        worker_args = [(i+1, chunk, True, job_id) for i, chunk in enumerate(chunks)]
        
        # Run parallel scraping
        all_results = []
        with Pool(processes=num_workers) as pool:
            worker_results = pool.map(worker_process, worker_args)
            for results in worker_results:
                all_results.extend(results)
        
        # Save results to Excel
        df = pd.DataFrame(all_results)
        df.to_excel(output_file, index=False, engine='openpyxl')
        
        jobs[job_id]['status'] = 'completed'
        jobs[job_id]['message'] = 'Scraping completed! Sending email...'
        
        # Send email with results
        send_email_with_attachment(email, output_file, total_codes)
        
        jobs[job_id]['message'] = 'Email sent successfully!'
        
    except Exception as e:
        jobs[job_id]['status'] = 'error'
        jobs[job_id]['message'] = f'Error: {str(e)}'
        print(f"Scraper error: {e}")


def send_email_with_attachment(to_email, file_path, total_codes):
    """Send email with Excel attachment"""
    try:
        # Email configuration (update with your SMTP settings)
        from_email = os.getenv('EMAIL_FROM', 'your-email@gmail.com')
        password = os.getenv('EMAIL_PASSWORD', 'your-app-password')
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = f'Price Scraper Results - {total_codes} OEM Codes'
        
        # Email body
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #2563eb;">Price Scraping Complete!</h2>
                <p>Your price comparison is ready.</p>
                <p><strong>Total OEM Codes Processed:</strong> {total_codes}</p>
                <p><strong>Websites Checked:</strong> InkStation, HotToner</p>
                <p>Please find the results attached as an Excel file.</p>
                <hr>
                <p style="color: #64748b; font-size: 12px;">
                    Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </p>
            </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))
        
        # Attach Excel file
        with open(file_path, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename=price_comparison_{datetime.now().strftime("%Y%m%d")}.xlsx'
        )
        msg.attach(part)
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(from_email, password)
        server.send_message(msg)
        server.quit()
        
        print(f"Email sent to {to_email}")
        
    except Exception as e:
        print(f"Email error: {e}")
        raise


@app.route('/api/scrape', methods=['POST'])
def start_scrape():
    """Start a new scraping job"""
    try:
        # Check if file and email are provided
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        email = request.form.get('email')
        
        if not email:
            return jsonify({'error': 'No email provided'}), 400
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only .xlsx and .xls allowed'}), 400
        
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        input_file = os.path.join(UPLOAD_FOLDER, f'{job_id}_{filename}')
        file.save(input_file)
        
        # Output file path
        output_file = os.path.join(RESULTS_FOLDER, f'{job_id}_results.xlsx')
        
        # Create job record
        jobs[job_id] = {
            'status': 'pending',
            'progress': {'current': 0, 'total': 0},
            'message': 'Job queued',
            'created_at': datetime.now().isoformat()
        }
        
        # Start scraping in background thread
        thread = threading.Thread(
            target=run_scraper_job,
            args=(job_id, input_file, output_file, email)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'job_id': job_id,
            'message': 'Scraping job started'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/status/<job_id>', methods=['GET'])
def get_status(job_id):
    """Get status of a scraping job"""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(jobs[job_id]), 200


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()}), 200


if __name__ == '__main__':
    print("🚀 Price Scraper API Starting...")
    print("📡 API URL: http://localhost:5000")
    print("📧 Make sure to set EMAIL_FROM and EMAIL_PASSWORD in .env")
    app.run(debug=True, host='0.0.0.0', port=5000)

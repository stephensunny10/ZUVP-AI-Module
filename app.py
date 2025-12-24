from flask import Flask, request, jsonify, render_template, send_file
import os
from dotenv import load_dotenv
from src.pipeline import ZUVPPipeline
from src.config import Config
from src.utils import setup_logging

# Load environment variables
load_dotenv()

logger = setup_logging()

app = Flask(__name__)
pipeline = ZUVPPipeline()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        result = pipeline.process_file(file)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@app.route('/api/drafts', methods=['GET'])
def get_drafts():
    drafts = pipeline.get_drafts()
    return jsonify(drafts)

@app.route('/api/approve/<draft_id>', methods=['POST'])
def approve_draft(draft_id):
    try:
        result = pipeline.approve_draft(draft_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear-cache', methods=['POST'])
def clear_cache():
    try:
        result = pipeline.clear_cache()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Clear cache error: {str(e)}")
        return jsonify({'error': f'Cache clearing failed: {str(e)}'}), 500

@app.route('/api/clear-drafts', methods=['POST'])
def clear_drafts():
    try:
        result = pipeline.clear_drafts()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<draft_id>/<doc_type>', methods=['GET'])
def download_document(draft_id, doc_type):
    try:
        file_path = pipeline.get_document_path(draft_id, doc_type)
        if not os.path.exists(file_path):
            return jsonify({'error': 'Document not found'}), 404
        
        filename = f"{doc_type}_{draft_id}.docx"
        return send_file(file_path, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
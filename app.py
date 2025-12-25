from flask import Flask, request, jsonify, render_template, send_file
import os
from dotenv import load_dotenv
from src.pipeline import ZUVPPipeline
from src.config import Config
from src.utils import setup_logging

# Optional folder monitoring
try:
    from src.folder_monitor import FolderMonitor
    FOLDER_MONITORING_AVAILABLE = True
except ImportError:
    FOLDER_MONITORING_AVAILABLE = False

# Load environment variables
load_dotenv()

logger = setup_logging()

app = Flask(__name__)
pipeline = ZUVPPipeline()

# Initialize folder monitoring if available
folder_monitor = None
if FOLDER_MONITORING_AVAILABLE:
    folder_monitor = FolderMonitor()
    folder_monitor.start_monitoring()
    logger.info("Folder monitoring started")
else:
    logger.warning("Folder monitoring disabled - install watchdog package")

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/simple')
def simple():
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

@app.route('/api/v1/submit', methods=['POST'])
def api_submit():
    """REST API endpoint for external file submissions"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided',
                'code': 'NO_FILE'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected',
                'code': 'EMPTY_FILE'
            }), 400
        
        result = pipeline.process_file(file)
        
        if result['status'] == 'draft_created':
            return jsonify({
                'success': True,
                'request_id': result['request_id'],
                'status': 'processed',
                'message': 'File processed successfully, draft created for review'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Processing failed'),
                'code': 'PROCESSING_ERROR'
            }), 422
            
    except Exception as e:
        logger.error(f"API submit error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 'SERVER_ERROR'
        }), 500

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

@app.route('/api/monitor/status', methods=['GET'])
def monitor_status():
    if not FOLDER_MONITORING_AVAILABLE or not folder_monitor:
        return jsonify({
            'monitoring': False,
            'watch_folder': 'N/A',
            'error': 'Folder monitoring not available'
        })
    
    return jsonify({
        'monitoring': folder_monitor.is_running(),
        'watch_folder': folder_monitor.watch_folder
    })

@app.route('/api/monitor/start', methods=['POST'])
def start_monitoring():
    if folder_monitor:
        folder_monitor.start_monitoring()
        return jsonify({'status': 'started'})
    return jsonify({'error': 'Monitoring not available'}), 400

@app.route('/api/monitor/stop', methods=['POST'])
def stop_monitoring():
    if folder_monitor:
        folder_monitor.stop_monitoring()
        return jsonify({'status': 'stopped'})
    return jsonify({'error': 'Monitoring not available'}), 400

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
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    finally:
        if folder_monitor:
            folder_monitor.stop_monitoring()
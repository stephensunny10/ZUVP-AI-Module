import os
import shutil
from werkzeug.utils import secure_filename
from src.config import Config
from src.utils import setup_logging

logger = setup_logging()

class IngestionModule:
    def __init__(self):
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    
    def save_file(self, file, request_id):
        """Save uploaded file and return path"""
        if not Config.allowed_file(file.filename):
            raise ValueError(f"File type not supported: {file.filename}")
        
        filename = secure_filename(file.filename)
        file_path = os.path.join(Config.UPLOAD_FOLDER, f"{request_id}_{filename}")
        file.save(file_path)
        
        logger.info(f"File saved: {file_path}")
        return file_path
    
    def monitor_folder(self):
        """Monitor Zadosti folder for new files"""
        if not os.path.exists(Config.ZADOSTI_FOLDER):
            os.makedirs(Config.ZADOSTI_FOLDER, exist_ok=True)
            return []
        
        files = []
        for filename in os.listdir(Config.ZADOSTI_FOLDER):
            if Config.allowed_file(filename):
                file_path = os.path.join(Config.ZADOSTI_FOLDER, filename)
                files.append(file_path)
        
        return files
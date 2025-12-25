import logging
import os
import hashlib
from datetime import datetime

def setup_logging():
    """Setup logging configuration"""
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"zuvp_{datetime.now().strftime('%Y%m%d')}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def generate_variable_symbol(request_id):
    """Generate Czech banking Variable Symbol from request_id"""
    hash_obj = hashlib.md5(request_id.encode())
    numeric_hash = int(hash_obj.hexdigest()[:8], 16)
    vs = str(numeric_hash)[:10]
    return vs

def calculate_duration_days(start_date, end_date):
    """Calculate duration in days between two dates"""
    try:
        if isinstance(start_date, str):
            start = datetime.strptime(start_date, '%Y-%m-%d')
        else:
            start = start_date
            
        if isinstance(end_date, str):
            end = datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end = end_date
            
        return (end - start).days + 1
    except:
        return 1
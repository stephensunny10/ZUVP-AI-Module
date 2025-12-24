import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Nebius AI Configuration
    NEBIUS_API_KEY = os.getenv('NEBIUS_API_KEY', '')
    NEBIUS_BASE_URL = "https://api.tokenfactory.nebius.com/v1"
    
    # Models
    LLM_MODEL = "Qwen/Qwen3-235B-A22B-Thinking-2507"
    VISION_MODEL = "Qwen/Qwen2.5-VL-72B-Instruct"
    
    # File handling
    UPLOAD_FOLDER = 'uploads'
    ZADOSTI_FOLDER = 'Zadosti'
    DRAFTS_FOLDER = 'drafts'
    TEMPLATES_FOLDER = 'templates/documents'
    
    # Cache directories
    VISION_CACHE_FOLDER = 'vision_cache'
    EXTRACTED_TEXT_CACHE_FOLDER = 'extracted_text_cache'
    
    # Fee calculation
    DEFAULT_RATE_PER_SQM_DAY = 10  # CZK
    
    # Supported file formats
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'docx', 'txt'}
    
    @staticmethod
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
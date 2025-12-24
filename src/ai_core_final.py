import os
import json
import hashlib
import requests
from pdf2image import convert_from_path
from PIL import Image
import base64
from io import BytesIO
from src.config import Config
from src.utils import setup_logging

logger = setup_logging()

class AICore:
    def __init__(self):
        self.api_key = Config.NEBIUS_API_KEY
        self.base_url = Config.NEBIUS_BASE_URL
        
    def extract_entities(self, file_path):
        """Extract entities from file using AI"""
        file_hash = self._get_file_hash(file_path)
        cache_path = os.path.join(Config.EXTRACTED_TEXT_CACHE_FOLDER, f"{file_hash}.json")
        
        # Check cache first
        if os.path.exists(cache_path):
            logger.info(f"Using cached extraction for {file_path}")
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Process file based on type
        if file_path.lower().endswith('.pdf'):
            extracted_data = self._process_pdf(file_path)
        elif file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
            extracted_data = self._process_image(file_path)
        else:
            extracted_data = self._process_text_file(file_path)
        
        # Cache result
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(extracted_data, f, ensure_ascii=False, indent=2)
        
        return extracted_data
    
    def _process_pdf(self, file_path):
        """Convert PDF to images and process with vision model as per requirements"""
        try:
            # Use pdf2image as specified in requirements
            images = convert_from_path(file_path)
            
            if images:
                logger.info(f"Converted PDF to {len(images)} images: {file_path}")
                # Process first page with Vision model
                return self._analyze_image_with_ai(images[0])
            else:
                logger.warning(f"No images extracted from PDF: {file_path}")
                return {"error": "No images extracted from PDF"}
                
        except Exception as e:
            logger.error(f"PDF processing failed: {str(e)}")
            # Fallback to text extraction if pdf2image fails
            try:
                import PyPDF2
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text()
                
                if text.strip():
                    logger.info(f"Fallback: extracted {len(text)} characters from PDF")
                    return self._analyze_text_with_ai(text)
                else:
                    return {"error": "No content extracted from PDF"}
            except Exception as fallback_error:
                logger.error(f"Fallback text extraction failed: {str(fallback_error)}")
                return {"error": f"PDF processing failed: {str(e)}"}
    
    def _process_image(self, file_path):
        """Process image file with vision model"""
        image = Image.open(file_path)
        return self._analyze_image_with_ai(image)
    
    def _process_text_file(self, file_path):
        """Process text file with LLM"""
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        return self._analyze_text_with_ai(text)
    
    def _analyze_image_with_ai(self, image):
        """Analyze image using Nebius Vision API with direct requests"""
        # Convert image to base64
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        prompt = """Extract the following information from this ZUVP (Special Use of Public Space) application form:
        - Applicant name (žadatel)
        - Company ID (IČO) if applicable
        - Contact details (phone, email, address)
        - Purpose of use (účel užívání)
        - Specific location (address/plot number)
        - Duration (start and end date)
        - Area in square meters if mentioned
        
        Return as JSON format."""
        
        payload = {
            "model": Config.VISION_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}}
                    ]
                }
            ],
            "max_tokens": 1000
        }
        
        return self._call_api(payload)
    
    def _analyze_text_with_ai(self, text):
        """Analyze text using Nebius LLM API with direct requests"""
        prompt = f"""Extract the following information from this ZUVP application text:
        - Applicant name
        - Company ID (IČO) if applicable  
        - Contact details
        - Purpose of use
        - Location
        - Duration (dates)
        - Area in square meters
        
        Text: {text}
        
        Return as JSON format."""
        
        payload = {
            "model": Config.LLM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000
        }
        
        return self._call_api(payload)
    
    def _call_api(self, payload):
        """Make direct API call to Nebius as specified in requirements"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(f"{self.base_url}/chat/completions", 
                                   headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Try to parse as JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # If not valid JSON, return as text
                return {"raw_response": content}
                
        except Exception as e:
            logger.error(f"API call failed: {str(e)}")
            return {"error": str(e)}
    
    def _get_file_hash(self, file_path):
        """Generate hash for file caching"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
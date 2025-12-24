import os
import json
import hashlib
from openai import OpenAI
from PIL import Image
import base64
from io import BytesIO
from src.config import Config
from src.utils import setup_logging

logger = setup_logging()

class AICore:
    def __init__(self):
        self.client = OpenAI(
            base_url=Config.NEBIUS_BASE_URL,
            api_key=Config.NEBIUS_API_KEY
        )
        
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
            extracted_data = self._process_pdf_with_text_extraction(file_path)
        elif file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
            extracted_data = self._process_image(file_path)
        else:
            extracted_data = self._process_text_file(file_path)
        
        # Cache result
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(extracted_data, f, ensure_ascii=False, indent=2)
        
        return extracted_data
    
    def _process_pdf_with_text_extraction(self, file_path):
        """Process PDF by reading text content and using LLM"""
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
            
            if text.strip():
                logger.info(f"Extracted {len(text)} characters from PDF: {file_path}")
                return self._analyze_text_with_ai(text)
            else:
                logger.warning(f"No text found in PDF: {file_path}")
                return {"error": "No text content found in PDF"}
                
        except Exception as e:
            logger.error(f"Error processing PDF {file_path}: {str(e)}")
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
        """Analyze image using Nebius Vision API"""
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        try:
            response = self.client.chat.completions.create(
                model=Config.VISION_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Extract the following information from this ZUVP (Special Use of Public Space) application form:
                                - Applicant name (žadatel)
                                - Company ID (IČO) if applicable
                                - Contact details (phone, email, address)
                                - Purpose of use (účel užívání)
                                - Specific location (address/plot number)
                                - Duration (start and end date)
                                - Area in square meters if mentioned
                                
                                Return as JSON format."""
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{image_base64}"}
                            }
                        ]
                    }
                ]
            )
            
            content = response.choices[0].message.content
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"raw_response": content}
                
        except Exception as e:
            logger.error(f"Vision API call failed: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_text_with_ai(self, text):
        """Analyze text using Nebius LLM API"""
        try:
            response = self.client.chat.completions.create(
                model=Config.LLM_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Extract the following information from this ZUVP application text:
                        - Applicant name
                        - Company ID (IČO) if applicable  
                        - Contact details
                        - Purpose of use
                        - Location
                        - Duration (dates)
                        - Area in square meters
                        
                        Text: {text}
                        
                        Return as JSON format."""
                    }
                ]
            )
            
            content = response.choices[0].message.content
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"raw_response": content}
                
        except Exception as e:
            logger.error(f"LLM API call failed: {str(e)}")
            return {"error": str(e)}
    
    def _get_file_hash(self, file_path):
        """Generate hash for file caching"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
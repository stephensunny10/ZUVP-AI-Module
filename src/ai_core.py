import os
import json
import hashlib
import requests
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
        print(f"\n=== PROCESSING FILE ===\nFile: {file_path}\nFile exists: {os.path.exists(file_path)}\n=== END FILE INFO ===")
        
        # COMPLETELY DISABLE CACHE FOR DEBUGGING
        # Process file based on type
        if file_path.lower().endswith('.pdf'):
            extracted_data = self._process_pdf_with_vision_model(file_path)
        elif file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
            extracted_data = self._process_image(file_path)
        else:
            extracted_data = self._process_text_file(file_path)
        
        print(f"\n=== EXTRACTION COMPLETE ===\nResult: {extracted_data}\n=== END EXTRACTION ===")
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
                print(f"\n=== PDF TEXT EXTRACTED ===\n{text}\n=== END PDF TEXT ===")
                return self._analyze_text_with_ai(text)
            else:
                logger.warning(f"No text found in PDF: {file_path}")
                return {"error": "No text content found in PDF"}
                
        except Exception as e:
            logger.error(f"Error processing PDF {file_path}: {str(e)}")
            return {"error": f"PDF processing failed: {str(e)}"}
    
    def _process_pdf_with_vision_model(self, file_path):
        """Process PDF by converting to images and using Vision model"""
        try:
            from pdf2image import convert_from_path
            print(f"\n=== ATTEMPTING PDF TO IMAGE CONVERSION ===\nFile: {file_path}\n=== END ATTEMPT ===")
            
            # Convert PDF to images
            images = convert_from_path(file_path)
            
            if images:
                print(f"\n=== PDF CONVERTED TO {len(images)} IMAGES ===\nProcessing with Vision model...\n=== END PDF INFO ===")
                # Process first page with Vision model
                return self._analyze_image_with_ai(images[0])
            else:
                logger.warning(f"No images generated from PDF: {file_path}")
                print(f"\n=== PDF CONVERSION FAILED ===\nFalling back to text extraction\n=== END FALLBACK ===")
                return self._process_pdf_with_text_extraction(file_path)
                
        except ImportError:
            logger.error("pdf2image not available, falling back to text extraction")
            print(f"\n=== PDF2IMAGE NOT AVAILABLE ===\nFalling back to text extraction\n=== END FALLBACK ===")
            return self._process_pdf_with_text_extraction(file_path)
        except Exception as e:
            logger.error(f"Error converting PDF to images {file_path}: {str(e)}")
            print(f"\n=== PDF CONVERSION ERROR ===\nError: {str(e)}\nFalling back to text extraction\n=== END FALLBACK ===")
            return self._process_pdf_with_text_extraction(file_path)
    
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
        
        print(f"\n=== IMAGE PROCESSING ===\nImage size: {image.size}\nProcessing with Vision model...\n=== END IMAGE INFO ===")
        
        payload = {
            "model": Config.VISION_MODEL,
            "messages": [
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
        }
        
        result = self._call_api(payload)
        print(f"\n=== VISION MODEL RESULT ===\n{result}\n=== END VISION RESULT ===")
        return result
    
    def _analyze_text_with_ai(self, text):
        """Analyze text using Nebius LLM API"""
        payload = {
            "model": Config.LLM_MODEL,
            "messages": [
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
        }
        
        return self._call_api(payload)
    
    def _call_api(self, payload):
        """Make direct API call to Nebius using requests"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            print(f"\n=== API REQUEST ===\nModel: {payload['model']}\nPayload: {json.dumps(payload, indent=2, ensure_ascii=False)}\n=== END REQUEST ===")
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=120  # Increased timeout to 2 minutes
            )
            response.raise_for_status()
            
            result = response.json()
            print(f"\n=== API RESPONSE ===\nFull Response: {json.dumps(result, indent=2, ensure_ascii=False)}\n=== END RESPONSE ===")
            
            if 'choices' not in result or not result['choices']:
                return {"error": "Invalid API response format"}
            
            content = result['choices'][0]['message']['content']
            print(f"\n=== EXTRACTED CONTENT ===\n{content}\n=== END CONTENT ===")
            
            # Try to parse as JSON
            try:
                # Remove markdown code blocks if present
                clean_content = content.strip()
                if clean_content.startswith('```json'):
                    clean_content = clean_content[7:]  # Remove ```json
                if clean_content.startswith('```'):
                    clean_content = clean_content[3:]   # Remove ```
                if clean_content.endswith('```'):
                    clean_content = clean_content[:-3]  # Remove closing ```
                clean_content = clean_content.strip()
                
                parsed_data = json.loads(clean_content)
                print(f"\n=== PARSED JSON DATA ===\n{json.dumps(parsed_data, indent=2, ensure_ascii=False)}\n=== END PARSED DATA ===")
                return parsed_data
            except json.JSONDecodeError:
                print(f"\n=== RAW RESPONSE (NOT JSON) ===\n{content}\n=== END RAW RESPONSE ===")
                return {"raw_response": content}
                
        except requests.exceptions.Timeout:
            error_msg = "API request timed out"
            logger.error(error_msg)
            print(f"\n=== API ERROR ===\n{error_msg}\n=== END ERROR ===")
            return {"error": error_msg}
        except requests.exceptions.RequestException as e:
            error_msg = f"API request failed: {str(e)}"
            logger.error(error_msg)
            print(f"\n=== API ERROR ===\n{error_msg}\n=== END ERROR ===")
            return {"error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            print(f"\n=== API ERROR ===\n{error_msg}\n=== END ERROR ===")
            return {"error": error_msg}
    
    def _get_file_hash(self, file_path):
        """Generate hash for file caching"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
import os
import json
import uuid
from datetime import datetime
from src.config import Config
from src.ingestion import IngestionModule
from src.ai_core import AICore
from src.document_engine import DocumentEngine
from src.utils import setup_logging

logger = setup_logging()

from src.validation import validate_zuvp_data

class ZUVPPipeline:
    def __init__(self):
        self.ingestion = IngestionModule()
        self.ai_core = AICore()
        self.document_engine = DocumentEngine()
        self._ensure_directories()
    
    def _ensure_directories(self):
        dirs = [Config.UPLOAD_FOLDER, Config.DRAFTS_FOLDER, 
                Config.VISION_CACHE_FOLDER, Config.EXTRACTED_TEXT_CACHE_FOLDER]
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
    
    def process_file(self, file):
        """Main processing pipeline"""
        request_id = str(uuid.uuid4())
        logger.info(f"Processing file {file.filename} with ID {request_id}")
        
        try:
            # Stage 1: Ingestion
            file_path = self.ingestion.save_file(file, request_id)
            
            # Stage 2: AI Extraction
            extracted_data = self.ai_core.extract_entities(file_path)
            
            # Stage 2.5: Validation
            validation_result = validate_zuvp_data(extracted_data)
            
            if not validation_result['is_zuvp_document']:
                return {
                    'request_id': request_id, 
                    'status': 'validation_failed',
                    'error': validation_result['error_message'],
                    'validation': validation_result
                }
            
            if not validation_result['is_valid']:
                return {
                    'request_id': request_id,
                    'status': 'incomplete_data', 
                    'warning': validation_result['error_message'],
                    'extracted_data': extracted_data,
                    'validation': validation_result
                }
            
            # Stage 3: Document Generation
            documents = self.document_engine.generate_documents(extracted_data, request_id)
            
            # Stage 4: Create Draft
            draft = self._create_draft(request_id, extracted_data, documents)
            
            logger.info(f"Successfully processed file {file.filename}")
            return {'request_id': request_id, 'status': 'draft_created', 'draft': draft}
            
        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {str(e)}")
            raise
    
    def _create_draft(self, request_id, extracted_data, documents):
        draft = {
            'id': request_id,
            'timestamp': datetime.now().isoformat(),
            'extracted_data': extracted_data,
            'documents': documents,
            'status': 'pending_approval'
        }
        
        draft_path = os.path.join(Config.DRAFTS_FOLDER, f"{request_id}.json")
        with open(draft_path, 'w', encoding='utf-8') as f:
            json.dump(draft, f, ensure_ascii=False, indent=2)
        
        return draft
    
    def get_drafts(self):
        drafts = []
        if os.path.exists(Config.DRAFTS_FOLDER):
            for filename in os.listdir(Config.DRAFTS_FOLDER):
                if filename.endswith('.json'):
                    with open(os.path.join(Config.DRAFTS_FOLDER, filename), 'r', encoding='utf-8') as f:
                        drafts.append(json.load(f))
        return drafts
    
    def approve_draft(self, draft_id):
        draft_path = os.path.join(Config.DRAFTS_FOLDER, f"{draft_id}.json")
        if not os.path.exists(draft_path):
            raise ValueError(f"Draft {draft_id} not found")
        
        with open(draft_path, 'r', encoding='utf-8') as f:
            draft = json.load(f)
        
        # Update status
        draft['status'] = 'approved'
        draft['approved_at'] = datetime.now().isoformat()
        
        with open(draft_path, 'w', encoding='utf-8') as f:
            json.dump(draft, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Draft {draft_id} approved")
        return {'status': 'approved', 'draft_id': draft_id}
        
    def clear_cache(self):
        """Clear only cache folders"""
        try:
            cleared_items = []
            
            # Clear cache folders only
            for cache_folder in [Config.EXTRACTED_TEXT_CACHE_FOLDER, Config.VISION_CACHE_FOLDER]:
                if os.path.exists(cache_folder):
                    for filename in os.listdir(cache_folder):
                        file_path = os.path.join(cache_folder, filename)
                        if os.path.isfile(file_path):
                            try:
                                os.remove(file_path)
                                cleared_items.append(f"cache: {filename}")
                            except Exception as e:
                                logger.warning(f"Could not remove cache file {filename}: {str(e)}")
            
            logger.info(f"Cleared {len(cleared_items)} cache items")
            return {'status': 'success', 'message': f'Cleared {len(cleared_items)} cache files'}
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return {'status': 'error', 'message': f'Error clearing cache: {str(e)}'}
    
    def clear_drafts(self):
        """Clear all draft files and cache"""
        try:
            cleared_items = []
            
            # Clear drafts
            if os.path.exists(Config.DRAFTS_FOLDER):
                for filename in os.listdir(Config.DRAFTS_FOLDER):
                    if filename.endswith('.json'):
                        try:
                            os.remove(os.path.join(Config.DRAFTS_FOLDER, filename))
                            cleared_items.append(f"draft: {filename}")
                        except Exception as e:
                            logger.warning(f"Could not remove draft {filename}: {str(e)}")
            
            # Clear cache folders
            for cache_folder in [Config.EXTRACTED_TEXT_CACHE_FOLDER, Config.VISION_CACHE_FOLDER]:
                if os.path.exists(cache_folder):
                    for filename in os.listdir(cache_folder):
                        file_path = os.path.join(cache_folder, filename)
                        if os.path.isfile(file_path):
                            try:
                                os.remove(file_path)
                                cleared_items.append(f"cache: {filename}")
                            except Exception as e:
                                logger.warning(f"Could not remove cache file {filename}: {str(e)}")
            
            # Clear uploads folder
            if os.path.exists(Config.UPLOAD_FOLDER):
                for filename in os.listdir(Config.UPLOAD_FOLDER):
                    file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
                    if os.path.isfile(file_path):
                        try:
                            os.remove(file_path)
                            cleared_items.append(f"upload: {filename}")
                        except Exception as e:
                            logger.warning(f"Could not remove upload file {filename}: {str(e)}")
            
            # Clear output folder
            if os.path.exists('output'):
                for filename in os.listdir('output'):
                    file_path = os.path.join('output', filename)
                    if os.path.isfile(file_path):
                        try:
                            os.remove(file_path)
                            cleared_items.append(f"output: {filename}")
                        except Exception as e:
                            logger.warning(f"Could not remove output file {filename}: {str(e)}")
            
            logger.info(f"Cleared {len(cleared_items)} items: {cleared_items}")
            return {'status': 'success', 'message': f'Cleared {len(cleared_items)} files - application reset to first-time state'}
        except Exception as e:
            logger.error(f"Error clearing data: {str(e)}")
            return {'status': 'error', 'message': f'Error clearing data: {str(e)}'}
    
    def get_document_path(self, draft_id, doc_type):
        """Get path to generated document"""
        draft_path = os.path.join(Config.DRAFTS_FOLDER, f"{draft_id}.json")
        if not os.path.exists(draft_path):
            raise ValueError(f"Draft {draft_id} not found")
        
        with open(draft_path, 'r', encoding='utf-8') as f:
            draft = json.load(f)
        
        if doc_type not in draft['documents']:
            raise ValueError(f"Document type {doc_type} not found")
        
        return draft['documents'][doc_type]
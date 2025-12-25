import os
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from src.pipeline import ZUVPPipeline
from src.utils import setup_logging

logger = setup_logging()

class ZUVPFileHandler(FileSystemEventHandler):
    def __init__(self, pipeline):
        self.pipeline = pipeline
        self.supported_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.docx', '.txt'}
    
    def on_created(self, event):
        if event.is_directory:
            return
        
        file_path = event.src_path
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext in self.supported_extensions:
            logger.info(f"New file detected: {file_path}")
            # Wait a moment for file to be fully written
            time.sleep(2)
            self._process_file(file_path)
    
    def _process_file(self, file_path):
        """Process file using ZUVP pipeline"""
        try:
            # Create a mock file object for pipeline processing
            class MockFile:
                def __init__(self, path):
                    self.filename = os.path.basename(path)
                    self.path = path
                    
                def save(self, destination):
                    # Copy file to destination
                    import shutil
                    shutil.copy2(self.path, destination)
                    return destination
            
            mock_file = MockFile(file_path)
            result = self.pipeline.process_file(mock_file)
            
            if result['status'] == 'draft_created':
                logger.info(f"Successfully processed {file_path} - Draft created")
                # Optionally move processed file to archive
                self._archive_file(file_path)
            else:
                logger.warning(f"Processing failed for {file_path}: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
    
    def _archive_file(self, file_path):
        """Move processed file to archive folder"""
        try:
            import shutil
            archive_dir = os.path.join(os.path.dirname(file_path), 'processed')
            os.makedirs(archive_dir, exist_ok=True)
            
            filename = os.path.basename(file_path)
            archive_path = os.path.join(archive_dir, filename)
            shutil.move(file_path, archive_path)
            logger.info(f"Archived processed file: {archive_path}")
        except Exception as e:
            logger.error(f"Failed to archive file {file_path}: {str(e)}")

class FolderMonitor:
    def __init__(self, watch_folder='Zadosti'):
        self.watch_folder = watch_folder
        self.pipeline = ZUVPPipeline()
        self.observer = None
        self.running = False
        
        # Ensure watch folder exists
        os.makedirs(watch_folder, exist_ok=True)
    
    def start_monitoring(self):
        """Start folder monitoring in background thread"""
        if self.running:
            logger.warning("Folder monitoring already running")
            return
        
        self.observer = Observer()
        event_handler = ZUVPFileHandler(self.pipeline)
        self.observer.schedule(event_handler, self.watch_folder, recursive=False)
        
        self.observer.start()
        self.running = True
        logger.info(f"Started monitoring folder: {self.watch_folder}")
    
    def stop_monitoring(self):
        """Stop folder monitoring"""
        if self.observer and self.running:
            self.observer.stop()
            self.observer.join()
            self.running = False
            logger.info("Stopped folder monitoring")
    
    def is_running(self):
        """Check if monitoring is active"""
        return self.running and self.observer and self.observer.is_alive()
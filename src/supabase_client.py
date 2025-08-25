"""
Supabase client module for database and storage operations.
"""
import os
import uuid
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pathlib import Path

from supabase import create_client, Client
from dotenv import load_dotenv

from utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Load environment variables
load_dotenv()

class SupabaseManager:
    """Manages Supabase database and storage operations."""
    
    def __init__(self):
        """Initialize Supabase client with environment variables."""
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
        self.storage_bucket = os.getenv("SUPABASE_STORAGE_BUCKET", "audio_files")
        self.audio_storage_path = os.getenv("AUDIO_STORAGE_PATH", "audio")
        
        if not self.supabase_url or not self.supabase_key:
            error_msg = "SUPABASE_URL and SUPABASE_KEY environment variables are required"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            # Use service key for admin operations, fallback to regular key
            key_to_use = self.supabase_service_key if self.supabase_service_key else self.supabase_key
            self.client: Client = create_client(self.supabase_url, key_to_use)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            logger.debug(traceback.format_exc())
            raise
    
    def create_files_table(self) -> bool:
        """
        Create the files table if it doesn't exist.
        Note: This function assumes the table is created via Supabase dashboard or SQL editor.
        
        Returns:
            bool: True if table exists and is accessible
        """
        try:
            # Test if we can access the files table
            test_response = self.client.table("files").select("count", count="exact").execute()
            logger.info("Files table exists and is accessible")
            return True
            
        except Exception as e:
            logger.error(f"Files table not accessible. Please create it manually: {str(e)}")
            logger.error("Create table SQL:")
            logger.error("""
            CREATE TABLE IF NOT EXISTS files (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                url TEXT NOT NULL,
                metadata JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """)
            logger.debug(traceback.format_exc())
            return False
    
    def upload_file(self, metadata: Dict[str, Any], mp3_path: str) -> Optional[str]:
        """
        Upload MP3 file to Supabase Storage and save metadata to Postgres.
        
        Args:
            metadata: Dictionary containing file metadata
            mp3_path: Local path to the MP3 file to upload
            
        Returns:
            str: File ID if successful, None if failed
        """
        if not os.path.exists(mp3_path):
            logger.error(f"MP3 file not found: {mp3_path}")
            return None
        
        try:
            # Generate unique filename for storage
            file_id = str(uuid.uuid4())
            original_filename = Path(mp3_path).name
            storage_path = f"{self.audio_storage_path}/{file_id}_{original_filename}"
            
            # Upload file to Supabase Storage
            with open(mp3_path, 'rb') as file:
                file_data = file.read()
                
            logger.debug(f"Uploading {mp3_path} to {storage_path}")
            
            # Upload to storage bucket
            storage_response = self.client.storage.from_(self.storage_bucket).upload(
                path=storage_path,
                file=file_data,
                file_options={"content-type": "audio/mpeg"}
            )
            
            # Check if upload was successful
            if storage_response:
                logger.info(f"Successfully uploaded file to storage: {storage_path}")
                
                # Get public URL for the uploaded file
                public_url = self.client.storage.from_(self.storage_bucket).get_public_url(storage_path)
                
                # Insert metadata into database
                db_data = {
                    "id": file_id,
                    "name": original_filename,
                    "type": "audio/mpeg",
                    "url": public_url,
                    "metadata": metadata,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                db_response = self.client.table("files").insert(db_data).execute()
                
                if db_response.data:
                    logger.info(f"Successfully saved metadata to database with ID: {file_id}")
                    return file_id
                else:
                    logger.error(f"Failed to save metadata to database: {db_response}")
                    return None
            else:
                logger.error(f"Failed to upload file to storage: {storage_response}")
                return None
                
        except Exception as e:
            logger.error(f"Error in upload_file for {mp3_path}: {str(e)}")
            logger.debug(traceback.format_exc())
            return None
    
    def list_files(self) -> List[Dict[str, Any]]:
        """
        Retrieve all file records from the files table.
        
        Returns:
            List[Dict]: List of all file records
        """
        try:
            response = self.client.table("files").select("*").order("created_at", desc=True).execute()
            
            if response.data:
                logger.info(f"Retrieved {len(response.data)} file records")
                return response.data
            else:
                logger.warning("No files found in database")
                return []
                
        except Exception as e:
            logger.error(f"Error retrieving files from database: {str(e)}")
            logger.debug(traceback.format_exc())
            return []
    
    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from both storage and database.
        
        Args:
            file_id: UUID of the file to delete
            
        Returns:
            bool: True if deletion was successful
        """
        try:
            # First get file info from database
            file_response = self.client.table("files").select("*").eq("id", file_id).execute()
            
            if not file_response.data:
                logger.warning(f"File with ID {file_id} not found in database")
                return False
            
            file_info = file_response.data[0]
            
            # Extract storage path from URL
            storage_path = file_info["url"].split(f"{self.storage_bucket}/")[-1]
            
            # Delete from storage
            storage_response = self.client.storage.from_(self.storage_bucket).remove([storage_path])
            
            # Delete from database
            db_response = self.client.table("files").delete().eq("id", file_id).execute()
            
            if db_response.data:
                logger.info(f"Successfully deleted file {file_id}")
                return True
            else:
                logger.error(f"Failed to delete file from database: {file_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting file {file_id}: {str(e)}")
            logger.debug(traceback.format_exc())
            return False


# Global instance
_supabase_manager = None

def get_supabase_manager() -> SupabaseManager:
    """Get or create global Supabase manager instance."""
    global _supabase_manager
    if _supabase_manager is None:
        _supabase_manager = SupabaseManager()
    return _supabase_manager

def upload_file(metadata: Dict[str, Any], mp3_path: str) -> Optional[str]:
    """
    Upload MP3 file to Supabase Storage and save metadata to Postgres.
    
    Args:
        metadata: Dictionary containing file metadata
        mp3_path: Local path to the MP3 file to upload
        
    Returns:
        str: File ID if successful, None if failed
    """
    try:
        manager = get_supabase_manager()
        return manager.upload_file(metadata, mp3_path)
    except Exception as e:
        logger.error(f"Error in upload_file: {str(e)}")
        logger.debug(traceback.format_exc())
        return None

def list_files() -> List[Dict[str, Any]]:
    """
    Retrieve all file records from the files table.
    
    Returns:
        List[Dict]: List of all file records
    """
    try:
        manager = get_supabase_manager()
        return manager.list_files()
    except Exception as e:
        logger.error(f"Error in list_files: {str(e)}")
        logger.debug(traceback.format_exc())
        return []

def initialize_database() -> bool:
    """
    Initialize the database by creating required tables.
    
    Returns:
        bool: True if initialization was successful
    """
    try:
        manager = get_supabase_manager()
        return manager.create_files_table()
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        logger.debug(traceback.format_exc())
        return False

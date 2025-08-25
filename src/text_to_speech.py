"""
Text-to-speech module for generating audio files and uploading to Supabase.
"""
import json
import os
import re
import traceback
import tempfile
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
from pathlib import Path

from gtts import gTTS
from gtts.tts import gTTSError

from utils.logger import get_logger
from src.supabase_client import upload_file

# Initialize logger
logger = get_logger(__name__)

def clean_filename(filename: str) -> str:
    """
    Clean filename by removing or replacing problematic characters.
    
    Args:
        filename: Original filename to clean
        
    Returns:
        Cleaned filename with only alphanumeric characters and underscores
    """
    try:
        if not filename or not isinstance(filename, str):
            logger.warning(f"Invalid filename provided: {filename}")
            return "unnamed"
            
        # Replace problematic characters
        cleaned = re.sub(r'[^\w\s-]', '_', filename)  # Replace non-word chars with underscore
        cleaned = re.sub(r'[-\s]+', '_', cleaned)     # Replace spaces and hyphens with underscore
        cleaned = cleaned.lower().strip('_')          # Convert to lowercase and strip underscores
        
        # Ensure filename is not empty after cleaning
        if not cleaned:
            logger.warning(f"Filename became empty after cleaning: {filename}")
            return f"unnamed_{int(datetime.now().timestamp())}"
            
        return cleaned
    except Exception as e:
        logger.error(f"Error cleaning filename '{filename}': {str(e)}")
        logger.debug(traceback.format_exc())
        return f"unnamed_{int(datetime.now().timestamp())}"

def create_tts_file(text: str, lang: str, filename: str) -> Optional[str]:
    """
    Create a TTS audio file using gTTS.
    
    Args:
        text: Text to convert to speech
        lang: Language code ('en', 'hi', 'gu')
        filename: Output filename
    
    Returns:
        str: Path to the created audio file, or None if failed
        
    Raises:
        ValueError: If language is not supported
        gTTSError: If there's an error with gTTS
        IOError: If there's an error saving the file
    """
    if not text or not text.strip():
        logger.warning("Empty or None text provided for TTS")
        return None
        
    if not lang or lang not in ['en', 'hi', 'gu']:
        error_msg = f"Unsupported language: {lang}. Must be 'en', 'hi', or 'gu'"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    try:
        logger.debug(f"Generating TTS for {len(text)} characters in {lang}")
        
        # Create TTS object based on language
        tts = gTTS(
            text=text, 
            lang=lang, 
            slow=False, 
            tld="co.in"  # Using Indian domain for better pronunciation of Indian languages
        )
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(filename)) or '.', exist_ok=True)
        
        # Save the audio file
        tts.save(filename)
        logger.info(f"Generated TTS file: {filename} ({os.path.getsize(filename) / 1024:.1f} KB)")
        return filename
    
    except gTTSError as e:
        logger.error(f"gTTS error generating speech: {str(e)}")
        logger.debug(traceback.format_exc())
        raise
    except IOError as e:
        logger.error(f"IOError saving TTS file {filename}: {str(e)}")
        logger.debug(traceback.format_exc())
        raise
    except Exception as e:
        logger.error(f"Unexpected error in create_tts_file: {str(e)}")
        logger.debug(traceback.format_exc())
        return None

def create_and_upload_tts_file(text: str, lang: str, filename: str, metadata: Dict[str, Any]) -> Optional[str]:
    """
    Create TTS file and upload to Supabase Storage.
    
    Args:
        text: Text to convert to speech
        lang: Language code ('en', 'hi', 'gu')
        filename: Filename for the audio file
        metadata: Metadata to store with the file
        
    Returns:
        str: Public URL of uploaded file, or None if failed
    """
    if not text or not text.strip():
        logger.warning("Empty or None text provided for TTS")
        return None
    
    try:
        # Create temporary file for TTS generation
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_path = temp_file.name
            
        # Generate TTS file
        tts_path = create_tts_file(text, lang, temp_path)
        if not tts_path:
            logger.error(f"Failed to generate TTS file for {filename}")
            return None
        
        # Prepare metadata for upload
        upload_metadata = {
            "filename": filename,
            "language": lang,
            "text_length": len(text),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "content_metadata": metadata
        }
        
        # Upload to Supabase
        file_id = upload_file(upload_metadata, tts_path)
        
        # Clean up temporary file
        try:
            os.unlink(temp_path)
        except OSError:
            pass  # Ignore cleanup errors
        
        if file_id:
            logger.info(f"Successfully uploaded TTS file {filename} with ID: {file_id}")
            return file_id  # Return file ID for reference
        else:
            logger.error(f"Failed to upload TTS file {filename} to Supabase")
            return None
            
    except Exception as e:
        logger.error(f"Error creating and uploading TTS file {filename}: {str(e)}")
        logger.debug(traceback.format_exc())
        return None

def process_brick_masonry_data(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process the brick masonry data and generate TTS files, uploading to Supabase.
    
    Args:
        input_data: Input JSON data with text content
    
    Returns:
        dict: Updated data with Supabase file IDs and URLs
    """
    if not input_data:
        logger.warning("No input data provided for TTS processing")
        return {}
    
    def process_section(section_key: str, section_data: Dict[str, Any], parent_key: str = "") -> None:
        """
        Recursively process sections and subsections to generate and upload TTS files.
        
        Args:
            section_key: Current section key
            section_data: Section data dictionary
            parent_key: Parent section key for hierarchical naming
        """
        if not section_data or not isinstance(section_data, dict):
            return
            
        try:
            # Create a clean filename from the section key
            clean_key = clean_filename(section_key)
            if parent_key:
                clean_parent = clean_filename(parent_key)
                file_prefix = f"{clean_parent}_{clean_key}"
            else:
                file_prefix = clean_key
            
            # Prepare metadata for this section
            section_metadata = {
                "section": section_key,
                "parent_section": parent_key,
                "type": "audio",
                "source": "document_processing"
            }
            
            # Generate and upload TTS for main text (English)
            if section_data.get("text"):
                try:
                    eng_filename = f"{file_prefix}_eng.mp3"
                    eng_metadata = {**section_metadata, "language": "en", "text_type": "original"}
                    eng_file_id = create_and_upload_tts_file(
                        section_data["text"], "en", eng_filename, eng_metadata
                    )
                    section_data["eng_speech_file_id"] = eng_file_id if eng_file_id else "Failed to generate"
                except Exception as e:
                    logger.error(f"Failed to generate English TTS for {section_key}: {str(e)}")
                    section_data["eng_speech_file_id"] = "Failed to generate"
            
            # Generate and upload TTS for Hindi text
            if section_data.get("hindi_text"):
                try:
                    hindi_filename = f"{file_prefix}_hindi.mp3"
                    hindi_metadata = {**section_metadata, "language": "hi", "text_type": "translation"}
                    hindi_file_id = create_and_upload_tts_file(
                        section_data["hindi_text"], "hi", hindi_filename, hindi_metadata
                    )
                    section_data["hindi_speech_file_id"] = hindi_file_id if hindi_file_id else "Failed to generate"
                except Exception as e:
                    logger.error(f"Failed to generate Hindi TTS for {section_key}: {str(e)}")
                    section_data["hindi_speech_file_id"] = "Failed to generate"
            
            # Generate and upload TTS for Gujarati text
            if section_data.get("guj_text"):
                try:
                    guj_filename = f"{file_prefix}_guj.mp3"
                    guj_metadata = {**section_metadata, "language": "gu", "text_type": "translation"}
                    guj_file_id = create_and_upload_tts_file(
                        section_data["guj_text"], "gu", guj_filename, guj_metadata
                    )
                    section_data["guj_speech_file_id"] = guj_file_id if guj_file_id else "Failed to generate"
                except Exception as e:
                    logger.error(f"Failed to generate Gujarati TTS for {section_key}: {str(e)}")
                    section_data["guj_speech_file_id"] = "Failed to generate"
            
            # Process subtopics recursively
            if "subtopics" in section_data and section_data["subtopics"]:
                for subtopic_key, subtopic_data in section_data["subtopics"].items():
                    process_section(subtopic_key, subtopic_data, section_key)
                    
        except Exception as e:
            logger.error(f"Error processing section {section_key}: {str(e)}")
            logger.debug(traceback.format_exc())
    
    try:
        # Create a deep copy of the input data to avoid modifying the original
        output_data = json.loads(json.dumps(input_data))
        
        # Process each main section
        total_sections = len(output_data)
        logger.info(f"Starting TTS generation and Supabase upload for {total_sections} sections")
        
        for i, (section_key, section_data) in enumerate(output_data.items(), 1):
            try:
                logger.info(f"Processing section {i}/{total_sections}: {section_key}")
                process_section(section_key, section_data)
            except Exception as e:
                logger.error(f"Failed to process section {section_key}: {str(e)}")
                logger.debug(traceback.format_exc())
        
        logger.info("TTS generation and upload completed successfully")
        return output_data
        
    except Exception as e:
        logger.error(f"Fatal error in process_brick_masonry_data: {str(e)}")
        logger.debug(traceback.format_exc())
        return input_data  # Return original data on fatal error

# Alternative function to process complete dataset
def process_complete_dataset(complete_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process the complete brick masonry dataset from the document.
    
    This is a wrapper around process_brick_masonry_data for backward compatibility.
    
    Args:
        complete_data: Complete dataset from the document
    
    Returns:
        dict: Processed data with TTS paths
    """
    logger.info("Processing complete dataset with TTS generation")
    return process_brick_masonry_data(complete_data)
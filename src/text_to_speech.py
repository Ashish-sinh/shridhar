"""
Text-to-speech module for generating audio files and uploading to Supabase.
"""
import asyncio
import json
import os
import re
import traceback
import tempfile
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timezone
from pathlib import Path

import edge_tts
from utils.logger import get_logger
from src.supabase_client import upload_file

# Initialize logger
logger = get_logger(__name__)

# Voice configuration
VOICE_MAPPING = {
    'en': 'en-IN-PrabhatNeural',
    'hi': 'hi-IN-MadhurNeural',
    'gu': 'gu-IN-NiranjanNeural'
}

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

async def create_tts_file(text: str, lang: str, filename: str) -> Optional[str]:
    """
    Create a TTS audio file using edge_tts.
    
    Args:
        text: Text to convert to speech
        lang: Language code ('en', 'hi', 'gu')
        filename: Output filename
    
    Returns:
        str: Path to the created audio file, or None if failed
        
    Raises:
        ValueError: If language is not supported
        Exception: If there's an error with edge_tts
    """
    if not text or not text.strip():
        logger.warning("Empty or None text provided for TTS")
        return None
        
    if not lang or lang not in VOICE_MAPPING:
        error_msg = f"Unsupported language: {lang}. Must be one of: {', '.join(VOICE_MAPPING.keys())}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    try:
        logger.debug(f"Generating TTS for {len(text)} characters in {lang}")
        
        # Get the appropriate voice
        voice = VOICE_MAPPING[lang]
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(filename)) or '.', exist_ok=True)
        
        # Generate and save the audio file
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(filename)
        
        logger.info(f"Generated TTS file: {filename} ({os.path.getsize(filename) / 1024:.1f} KB)")
        return filename
    
    except Exception as e:
        logger.error(f"Error generating TTS with edge_tts: {str(e)}")
        logger.debug(traceback.format_exc())
        raise

async def create_and_upload_tts_file(text: str, lang: str, filename: str, metadata: Dict[str, Any]) -> Optional[str]:
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
    
    temp_path = None
    try:
        # Create temporary file for TTS generation
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_path = temp_file.name
        
        # Generate TTS file
        tts_path = await create_tts_file(text, lang, temp_path)
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
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        except OSError as e:
            logger.warning(f"Failed to clean up temporary file {temp_path}: {str(e)}")
        
        if file_id:
            logger.info(f"Successfully uploaded TTS file {filename} with ID: {file_id}")
            return file_id
        else:
            logger.error(f"Failed to upload TTS file {filename} to Supabase")
            return None
            
    except Exception as e:
        logger.error(f"Error creating and uploading TTS file {filename}: {str(e)}")
        logger.debug(traceback.format_exc())
        return None
    finally:
        # Ensure temporary file is cleaned up even if an error occurs
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError:
                pass

async def process_brick_masonry_data_async(input_data: Dict[str, Any]) -> Dict[str, Any]:
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
    
    async def process_section(section_key: str, section_data: Dict[str, Any], parent_key: str = "") -> None:
        """
        Recursively process sections and subsections to generate and upload TTS files.
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
            
            # Process each language
            for lang, lang_key in [('en', 'text'), ('hi', 'hindi_text'), ('gu', 'guj_text')]:
                if lang_key in section_data and section_data[lang_key]:
                    try:
                        file_key = f"{lang}_speech_file_id"
                        filename = f"{file_prefix}_{lang}.mp3"
                        lang_metadata = {**section_metadata, "language": lang, "text_type": "original" if lang == 'en' else "translation"}
                        
                        file_id = await create_and_upload_tts_file(
                            section_data[lang_key], 
                            lang, 
                            filename, 
                            lang_metadata
                        )
                        section_data[file_key] = file_id if file_id else "Failed to generate"
                    except Exception as e:
                        logger.error(f"Failed to generate {lang.upper()} TTS for {section_key}: {str(e)}")
                        section_data[f"{lang}_speech_file_id"] = "Failed to generate"
            
            # Process subtopics recursively
            if "subtopics" in section_data and section_data["subtopics"]:
                for subtopic_key, subtopic_data in section_data["subtopics"].items():
                    await process_section(subtopic_key, subtopic_data, section_key)
                    
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
                await process_section(section_key, section_data)
            except Exception as e:
                logger.error(f"Failed to process section {section_key}: {str(e)}")
                logger.debug(traceback.format_exc())
        
        logger.info("TTS generation and upload completed successfully")
        return output_data
        
    except Exception as e:
        logger.error(f"Fatal error in process_brick_masonry_data: {str(e)}")
        logger.debug(traceback.format_exc())
        return input_data  # Return original data on fatal error

def process_brick_masonry_data(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Synchronous wrapper for process_brick_masonry_data_async.
    Handles both cases: when called from sync and async contexts.
    """
    try:
        # Try to get the running event loop
        loop = asyncio.get_running_loop()
    except RuntimeError:  # No event loop running
        loop = None
    
    if loop and loop.is_running():
        # If there's a running event loop, create a task and wait for it
        future = asyncio.create_task(process_brick_masonry_data_async(input_data))
        # Return the future, allowing the caller to await it if needed
        return future
    else:
        # If no event loop is running, create one and run the async function
        return asyncio.run(process_brick_masonry_data_async(input_data))

# For backward compatibility
def process_complete_dataset(complete_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process the complete brick masonry dataset from the document.
    
    Args:
        complete_data: Complete dataset from the document
    
    Returns:
        dict: Processed data with TTS paths
    """
    logger.info("Processing complete dataset with TTS generation")
    return process_brick_masonry_data(complete_data)
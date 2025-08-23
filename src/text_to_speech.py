"""
Text-to-speech module for generating audio files from text content.
"""
import json
import os
import re
import traceback
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from gtts import gTTS
from gtts.tts import gTTSError

from utils.logger import get_logger

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

def process_brick_masonry_data(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process the brick masonry data and generate TTS files.
    
    Args:
        input_data: Input JSON data with text content
    
    Returns:
        dict: Updated data with TTS file paths
    """
    if not input_data:
        logger.warning("No input data provided for TTS processing")
        return {}
    
    # Create output directory for audio files
    audio_dir = "brick_masonry_audio"
    try:
        os.makedirs(audio_dir, exist_ok=True)
        logger.info(f"Using audio directory: {os.path.abspath(audio_dir)}")
    except Exception as e:
        logger.error(f"Failed to create audio directory {audio_dir}: {str(e)}")
        logger.debug(traceback.format_exc())
        return input_data  # Return original data on error
    
    def process_section(section_key: str, section_data: Dict[str, Any], parent_key: str = "") -> None:
        """
        Recursively process sections and subsections to generate TTS files.
        
        Args:
            section_key: Current section key
            section_data: Section data dictionary
            parent_key: Parent section key for hierarchical naming
        """
        if not section_data or not isinstance(section_data, dict):
            return
            
        try:
            # Create a clean filename from the section key - handle all problematic characters
            clean_key = clean_filename(section_key)
            if parent_key:
                clean_parent = clean_filename(parent_key)
                file_prefix = f"{clean_parent}_{clean_key}"
            else:
                file_prefix = clean_key
            
            # Generate TTS for main text (English)
            if section_data.get("text"):
                try:
                    eng_filename = f"{audio_dir}/{file_prefix}_eng.mp3"
                    eng_path = create_tts_file(section_data["text"], "en", eng_filename)
                    section_data["eng_speech_path"] = eng_path if eng_path else "Failed to generate"
                except Exception as e:
                    logger.error(f"Failed to generate English TTS for {section_key}: {str(e)}")
                    section_data["eng_speech_path"] = "Failed to generate"
            
            # Generate TTS for Hindi text
            if section_data.get("hindi_text"):
                try:
                    hindi_filename = f"{audio_dir}/{file_prefix}_hindi.mp3"
                    hindi_path = create_tts_file(section_data["hindi_text"], "hi", hindi_filename)
                    section_data["hindi_speech_path"] = hindi_path if hindi_path else "Failed to generate"
                except Exception as e:
                    logger.error(f"Failed to generate Hindi TTS for {section_key}: {str(e)}")
                    section_data["hindi_speech_path"] = "Failed to generate"
            
            # Generate TTS for Gujarati text
            if section_data.get("guj_text"):
                try:
                    guj_filename = f"{audio_dir}/{file_prefix}_guj.mp3"
                    guj_path = create_tts_file(section_data["guj_text"], "gu", guj_filename)
                    section_data["guj_speech_path"] = guj_path if guj_path else "Failed to generate"
                except Exception as e:
                    logger.error(f"Failed to generate Gujarati TTS for {section_key}: {str(e)}")
                    section_data["guj_speech_path"] = "Failed to generate"
            
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
        logger.info(f"Starting TTS generation for {total_sections} sections")
        
        for i, (section_key, section_data) in enumerate(output_data.items(), 1):
            try:
                logger.info(f"Processing section {i}/{total_sections}: {section_key}")
                process_section(section_key, section_data)
            except Exception as e:
                logger.error(f"Failed to process section {section_key}: {str(e)}")
                logger.debug(traceback.format_exc())
        
        logger.info("TTS generation completed successfully")
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
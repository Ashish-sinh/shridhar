"""
LLM-based text translation module with comprehensive error handling and logging.
"""
import json
import os
import traceback
from typing import Dict, Any, Optional, Union

from agno.agent import Agent
from agno.models.groq import Groq
from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv

from utils.logger import get_logger
from config.configuration import SYSTEM_PROMPT

# Initialize logger
logger = get_logger(__name__)

# Load environment variables
load_dotenv()

class SupportResult(BaseModel):
    """Pydantic model for LLM translation results."""
    gujrati_translation: str = Field(
        description="Gujarati translation of the text while keeping technical terms in English"
    )
    hindi_translation: str = Field(
        description="Hindi translation of the text while keeping technical terms in English"
    )

def get_support_agent() -> Agent:
    """
    Initialize and return a translation agent.
    
    Returns:
        Agent: Configured translation agent
    """
    try:
        logger.info("Initializing translation agent")
        agent = Agent(
            model=Groq(id="meta-llama/llama-4-scout-17b-16e-instruct"),
            system_message=SYSTEM_PROMPT,
            response_model=SupportResult,
            retries=10,
            add_datetime_to_instructions=True,
        )
        logger.debug("Successfully initialized translation agent")
        return agent
    except Exception as e:
        logger.error(f"Failed to initialize translation agent: {str(e)}")
        logger.debug(traceback.format_exc())
        raise

def translate_text_with_agent(text: str, agent: Agent) -> tuple[str, str]:
    """
    Translate text using the agent and return (hindi_text, guj_text)
    
    Args:
        text: Text to translate
        agent: Translation agent
        
    Returns:
        Tuple of (hindi_text, gujrati_text)
    """
    try:
        if not text or not text.strip():
            logger.warning("Empty or None text provided for translation")
            return "", ""
        
        logger.debug(f"Translating text: {text[:100]}...")
        
        response = agent.run(text)
        
        if not response or not response.content:
            logger.error("No valid response from translation agent")
            return "", ""
            
        logger.debug("Translation completed successfully")
        return response.content.hindi_translation, response.content.gujrati_translation
    
    except Exception as e:
        logger.error(f"Error in translate_text_with_agent: {str(e)}")
        logger.debug(traceback.format_exc())
        return "", ""

def add_translations_to_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add translations to the provided data dictionary.
    
    Args:
        data: Input data dictionary
        
    Returns:
        Dictionary with added translations
    """
    if not data:
        logger.warning("No data provided for translation")
        return {}
        
    try:
        agent = get_support_agent()
        return process_json_with_translations(data, agent)
    except Exception as e:
        logger.error(f"Error adding translations: {str(e)}")
        logger.debug(traceback.format_exc())
        raise

def process_json_with_translations(data: Dict[str, Any], agent: Agent) -> Dict[str, Any]:
    """
    Recursively process JSON data and add translations for 'text' fields.
    
    Args:
        data: Input data dictionary
        agent: Translation agent
        
    Returns:
        Processed data with translations
    """
    if not data:
        return {}
        
    try:
        if isinstance(data, dict):
            processed = {}
            for key, value in data.items():
                if key == 'text' and isinstance(value, str) and value.strip():
                    # Translate the text content
                    hindi_text, guj_text = translate_text_with_agent(value, agent)
                    processed.update({
                        'text': value,
                        'hindi_text': hindi_text,
                        'guj_text': guj_text
                    })
                elif isinstance(value, (dict, list)):
                    # Recursively process nested structures
                    processed[key] = process_json_with_translations(value, agent)
                else:
                    processed[key] = value
            return processed
        elif isinstance(data, list):
            return [process_json_with_translations(item, agent) for item in data]
        return data
    except Exception as e:
        logger.error(f"Error in process_json_with_translations: {str(e)}")
        logger.debug(traceback.format_exc())
        return data

def add_translations(input_data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Main function to add translations to the input data.
    
    Args:
        input_data: Either a file path (str) or a dictionary containing the data to translate
            
    Returns:
        Dictionary with added translations
    """
    try:
        # Handle both file path and direct dictionary input
        if isinstance(input_data, str):
            with open(input_data, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = input_data
        
        # Add translations and return the result
        return add_translations_to_data(data)
        
    except Exception as e:
        logger.error(f"Error in add_translations: {str(e)}")
        logger.debug(traceback.format_exc())
        raise

def main():
    # Example usage
    input_data = {
        "text": "Hello, world!",
        "subtopics": [
            {"text": "This is a subtopic"},
            {"text": "This is another subtopic"}
        ]
    }
    add_translations(input_data)

if __name__ == "__main__":
    main()
import json 
import os
from agno.agent import Agent
from agno.models.groq import Groq
from pydantic import BaseModel, Field
from dotenv import load_dotenv 
from config.configuration import SYSTEM_PROMPT

load_dotenv()

# result output schema from the LLM
class SupportResult(BaseModel):
    gujrati_translation: str = Field(description="Gujrati translation of the text while keeping the technical words in english")
    hindi_translation: str = Field(description="Hindi translation of the text while keeping the technical words in english") 

def get_support_agent() -> Agent:
    return Agent(
        model=Groq(id="meta-llama/llama-4-scout-17b-16e-instruct"),
        system_message=SYSTEM_PROMPT,
        response_model=SupportResult,
        retries=10,
        add_datetime_to_instructions=True,
    )

def translate_text_with_agent(text: str, agent: Agent) -> tuple[str, str]:
    """
    Translate text using the agent and return (hindi_text, guj_text)
    """
    try:
        if not text or text.strip() == "":
            return "", ""
        
        print(f"\nTranslating text: {text[:100]}...")
        
        # Run the agent and get the response
        response = agent.run(text)

        print(response.content.gujrati_translation)
        print(response.content.hindi_translation)
        
        return response.content.gujrati_translation, response.content.hindi_translation
    
    except Exception as e:
        print(f"Error in translate_text_with_agent: {e}")
        return " "," "

def process_json_with_translations(data: dict[str, any], agent: Agent) -> dict[str, any]:
    """
    Recursively process JSON data and add translations for 'text' fields
    """
    processed_data = {}
    
    for key, value in data.items():
        if isinstance(value, dict):
            processed_item = {}
            
            # Check if this dict has 'text' and 'subtopics' structure
            if 'text' in value:
                text_content = value['text']
                
                # Translate the text
                hindi_text, guj_text = translate_text_with_agent(text_content, agent)
                
                # Add original and translated texts
                processed_item['text'] = text_content
                processed_item['hindi_text'] = hindi_text
                processed_item['guj_text'] = guj_text
                
                # Handle subtopics recursively
                if 'subtopics' in value:
                    processed_item['subtopics'] = process_json_with_translations(value['subtopics'], agent)
                else:
                    processed_item['subtopics'] = {}
            else:
                # If it doesn't have the expected structure, process recursively
                processed_item = process_json_with_translations(value, agent)
            
            processed_data[key] = processed_item
        else:
            # If it's not a dict, keep it as is
            processed_data[key] = value
    
    return processed_data

def translate_brick_masonry_document(json_data: dict[str, any]) -> dict[str, any]:
    """
    Main function to translate the brick masonry document
    
    Args:
        json_data: The input JSON data with the document structure
    
    Returns:
        dict with original text plus hindi_text and guj_text for each text field
    """
    
    # Initialize the agent
    agent = get_support_agent()
    
    # Process the JSON data
    translated_data = process_json_with_translations(json_data, agent)
    
    return translated_data

# Example usage function
def main():
    # Sample data (your input format)
    sample_data = json.load(open("/Users/apple/shridhar/test.json"))
    
    try:
        translated_result = translate_brick_masonry_document(sample_data)
        
        # Print the result
        print(json.dumps(translated_result, indent=2, ensure_ascii=False))
        
        # Save to file if needed
        with open('translated_document.json', 'w', encoding='utf-8') as f:
            json.dump(translated_result, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
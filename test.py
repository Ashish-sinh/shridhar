from src.llm_parsing import add_translations
from src.text_to_speech import process_complete_dataset
from src.doc_extractor import extract_json_from_doc
from pprint import pprint
import json

if __name__ == "__main__":

    #extract json from doc
    structure = extract_json_from_doc("data/demo.docx", "text_extracted.json")
    pprint(structure)

    structure_with_translation = add_translations("text_extracted.json", "translated_document.json") 
    pprint(structure_with_translation)

    processed_complete_data = process_complete_dataset(structure_with_translation)
    pprint(processed_complete_data)
    # Save the result
    
    with open('complete_brick_masonry_with_tts.json', 'w', encoding='utf-8') as f:
        json.dump(processed_complete_data, f, indent=2, ensure_ascii=False)
        
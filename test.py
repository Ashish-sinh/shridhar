import json
from pprint import pprint
from pathlib import Path

from src.llm_parsing import add_translations
from src.text_to_speech import process_complete_dataset
from src.doc_extractor import extract_json_from_doc

def main():
    try:
        # 1. Extract JSON from DOCX
        print("Extracting content from DOCX...")
        extracted_data = extract_json_from_doc(
            "data/demo.docx",
            output_file="text_extracted.json"  # Optional: save intermediate result
        )
        
        # 2. Add translations to the extracted data
        print("\nAdding translations...")
        translated_data = add_translations(
            extracted_data,  # Pass the data directly
            output_file="translated_document.json"  # Optional: save intermediate result
        )
        
        # 3. Generate TTS for the translated data
        print("\nGenerating TTS files...")
        final_data = process_complete_dataset(translated_data)
        
        # 4. Save the final result
        output_path = 'complete_brick_masonry_with_tts.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Processing complete! Final output saved to: {Path(output_path).resolve()}")
        
    except Exception as e:
        print(f"\n❌ An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
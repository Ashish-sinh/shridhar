import json
from pprint import pprint
from pathlib import Path

from src.llm_parsing import add_translations
from src.text_to_speech import process_complete_dataset
from src.doc_extractor import extract_json_from_doc
from src.supabase_client import list_files, initialize_database

def test_supabase_integration():
    """Test Supabase database initialization and file listing."""
    print("🔧 Testing Supabase integration...")
    
    try:
        # Initialize Supabase database
        print("\n1. Initializing Supabase database...")
        if initialize_database():
            print("✅ Database initialized successfully")
        else:
            print("❌ Database initialization failed")
            return
        
        # Test file listing
        print("\n2. Listing files from Supabase...")
        files = list_files()
        print(f"📁 Found {len(files)} files in database")
        
        if files:
            print("\n📋 File listing:")
            for i, file_info in enumerate(files[:5], 1):  # Show first 5 files
                print(f"  {i}. {file_info.get('name', 'N/A')} ({file_info.get('type', 'N/A')})")
                print(f"     Created: {file_info.get('created_at', 'N/A')}")
                print(f"     URL: {file_info.get('url', 'N/A')[:50]}...")
                print()
            
            if len(files) > 5:
                print(f"   ... and {len(files) - 5} more files")
        else:
            print("   No files found in database")
            
    except Exception as e:
        print(f"❌ Supabase test failed: {str(e)}")
        import traceback
        traceback.print_exc()

def process_document():
    """Process document with full pipeline including Supabase upload."""
    print("📄 Starting document processing with Supabase integration...")
    
    try:
        # 1. Extract JSON from DOCX
        print("\n1. Extracting content from DOCX...")
        extracted_data = extract_json_from_doc("data/demo.docx")
        print(f"   ✅ Extracted {len(extracted_data)} main topics")
        
        # Save extracted data to a file if needed (optional for debugging)
        with open('text_extracted.json', 'w', encoding='utf-8') as f:
            json.dump(extracted_data, f, indent=2, ensure_ascii=False)
        print("   💾 Saved extracted data to text_extracted.json")
        
        # 2. Add translations to the extracted data
        print("\n2. Adding translations...")
        translated_data = add_translations(extracted_data)
        print("   ✅ Added Hindi and Gujarati translations")
        
        # Save translated data to a file if needed (optional for debugging)
        with open('translated_document.json', 'w', encoding='utf-8') as f:
            json.dump(translated_data, f, indent=2, ensure_ascii=False)
        print("   💾 Saved translated data to translated_document.json")
        
        # 3. Generate TTS and upload to Supabase
        print("\n3. Generating TTS files and uploading to Supabase...")
        final_data = process_complete_dataset(translated_data)
        print("   ✅ Generated TTS files and uploaded to Supabase")
        
        # 4. Save the final result
        output_path = 'complete_processing_with_supabase.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n🎉 Processing complete! Final output saved to: {Path(output_path).resolve()}")
        
        # 5. Show updated file count
        print("\n4. Checking uploaded files...")
        files = list_files()
        print(f"   📁 Total files in Supabase: {len(files)}")
        
    except Exception as e:
        print(f"\n❌ An error occurred during processing: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Main function to run tests and document processing."""
    print("🚀 Shridhar Document Processing with Supabase Integration")
    print("=" * 60)
    
    # Test Supabase integration first
    test_supabase_integration()
    
    print("\n" + "=" * 60)
    
    # Ask user if they want to process a document
    try:
        response = input("\nDo you want to process the demo document? (y/n): ")
        if response.lower() in ['y', 'yes']:
            process_document()
        else:
            print("Skipping document processing.")
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"Error getting user input: {e}")

if __name__ == "__main__":
    main()
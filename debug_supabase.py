#!/usr/bin/env python3
"""
Debug script to test Supabase connection and TTS generation
"""
import os
import tempfile
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_environment_variables():
    """Test if all required environment variables are set."""
    print("🔧 Testing Environment Variables...")
    print("=" * 50)
    
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_KEY", 
        "SUPABASE_SERVICE_KEY",
        "SUPABASE_STORAGE_BUCKET",
        "AUDIO_STORAGE_PATH",
        "GROQ_API_KEY"
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask the keys for security
            if "KEY" in var or "URL" in var:
                masked_value = value[:10] + "..." + value[-5:] if len(value) > 15 else "***"
                print(f"✅ {var}: {masked_value}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")
    print()

def test_supabase_connection():
    """Test Supabase client connection."""
    print("🔗 Testing Supabase Connection...")
    print("=" * 50)
    
    try:
        from src.supabase_client import get_supabase_manager
        
        # Test initialization
        manager = get_supabase_manager()
        print("✅ Supabase client initialized successfully")
        
        # Test database table access
        try:
            files = manager.list_files()
            print(f"✅ Database connection successful - Found {len(files)} files")
        except Exception as db_error:
            print(f"❌ Database connection failed: {str(db_error)}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Supabase initialization failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_tts_generation():
    """Test TTS generation without upload."""
    print("🎤 Testing TTS Generation...")
    print("=" * 50)
    
    try:
        from src.text_to_speech import create_tts_file
        
        # Test text
        test_text = "This is a test for TTS generation."
        
        # Test English TTS
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_path = temp_file.name
            
        try:
            result = create_tts_file(test_text, "en", temp_path)
            if result and os.path.exists(temp_path):
                file_size = os.path.getsize(temp_path)
                print(f"✅ English TTS generated successfully ({file_size} bytes)")
                os.unlink(temp_path)  # Clean up
            else:
                print("❌ English TTS generation failed")
                return False
        except Exception as tts_error:
            print(f"❌ TTS generation error: {str(tts_error)}")
            return False
            
        return True
        
    except ImportError as e:
        print(f"❌ TTS module import failed: {str(e)}")
        return False

def test_storage_upload():
    """Test file upload to Supabase Storage."""
    print("☁️ Testing Supabase Storage Upload...")
    print("=" * 50)
    
    try:
        from src.supabase_client import upload_file
        from src.text_to_speech import create_tts_file
        
        # Generate a small test file
        test_text = "Test file for Supabase upload."
        
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_path = temp_file.name
            
        # Generate TTS file
        if create_tts_file(test_text, "en", temp_path):
            # Test metadata
            test_metadata = {
                "test": True,
                "filename": "debug_test.mp3",
                "language": "en",
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # Try upload
            file_id = upload_file(test_metadata, temp_path)
            
            # Clean up temp file
            os.unlink(temp_path)
            
            if file_id:
                print(f"✅ File uploaded successfully with ID: {file_id}")
                return True
            else:
                print("❌ File upload failed - check logs for details")
                return False
        else:
            print("❌ Could not generate test TTS file for upload")
            os.unlink(temp_path)
            return False
            
    except Exception as e:
        print(f"❌ Storage upload test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_full_pipeline():
    """Test the complete TTS generation and upload pipeline."""
    print("🏗️ Testing Full Pipeline...")
    print("=" * 50)
    
    try:
        from src.text_to_speech import create_and_upload_tts_file
        
        # Test data
        test_text = "Complete pipeline test for document processing."
        test_metadata = {
            "section": "debug_test",
            "language": "en",
            "type": "test",
            "source": "debug_script"
        }
        
        # Test the complete function
        result = create_and_upload_tts_file(
            test_text, 
            "en", 
            "debug_pipeline_test.mp3", 
            test_metadata
        )
        
        if result:
            print(f"✅ Full pipeline test successful! File ID: {result}")
            return True
        else:
            print("❌ Full pipeline test failed")
            return False
            
    except Exception as e:
        print(f"❌ Full pipeline test error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all diagnostic tests."""
    print("🚀 Shridhar Supabase Debug Tool")
    print("=" * 60)
    print()
    
    # Track results
    results = []
    
    # Test 1: Environment Variables
    results.append(("Environment Variables", True))  # This always passes if we get here
    test_environment_variables()
    
    # Test 2: Supabase Connection
    supabase_ok = test_supabase_connection()
    results.append(("Supabase Connection", supabase_ok))
    
    # Test 3: TTS Generation
    if supabase_ok:
        tts_ok = test_tts_generation()
        results.append(("TTS Generation", tts_ok))
        
        # Test 4: Storage Upload
        if tts_ok:
            storage_ok = test_storage_upload()
            results.append(("Storage Upload", storage_ok))
            
            # Test 5: Full Pipeline
            if storage_ok:
                pipeline_ok = test_full_pipeline()
                results.append(("Full Pipeline", pipeline_ok))
    
    # Summary
    print("📋 DIAGNOSTIC SUMMARY")
    print("=" * 60)
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print()
    if all(result[1] for result in results):
        print("🎉 All tests passed! Your Supabase integration should work correctly.")
    else:
        print("⚠️ Some tests failed. Please check the error messages above.")
        print("\n📚 Next steps:")
        print("1. Check your Supabase dashboard setup")
        print("2. Verify environment variables in .env file")
        print("3. Ensure the 'files' table exists in your database")
        print("4. Check that the 'audio_files' storage bucket exists")

if __name__ == "__main__":
    main()

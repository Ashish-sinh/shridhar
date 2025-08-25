# Shridhar - Document Processing with Supabase Integration

A production-ready FastAPI application that processes DOCX documents, translates content to Hindi and Gujarati using AI, generates text-to-speech audio files, and stores everything in Supabase.

## 🚀 Features

- **Document Processing**: Extract structured content from DOCX files
- **AI Translation**: Translate to Hindi and Gujarati using Groq LLM (Llama 4 Scout)
- **Text-to-Speech**: Generate audio files in English, Hindi, and Gujarati
- **Cloud Storage**: Store audio files in Supabase Storage with metadata in PostgreSQL
- **REST API**: Production-ready FastAPI endpoints
- **Monitoring**: Health checks, metrics, and comprehensive logging

## 🏗️ Architecture

```
DOCX Upload → Extract Topics → AI Translation → Generate TTS → Upload to Supabase
     ↓              ↓              ↓              ↓              ↓
   FastAPI      doc_extractor   llm_parsing   text_to_speech   supabase_client
```

## 📋 Requirements

- Python 3.13+
- Supabase account and project
- Groq API key for LLM translations

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd shridhar
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   # or using uv
   uv sync
   ```

3. **Set up environment variables:**
   Copy and update the `.env` file with your credentials:
   ```env
   # Groq API for LLM
   GROQ_API_KEY="your_groq_api_key"
   
   # Supabase Configuration
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your_public_key
   SUPABASE_SERVICE_KEY=your_service_key
   SUPABASE_STORAGE_BUCKET=audio_files
   AUDIO_STORAGE_PATH=audio
   ```

4. **Set up Supabase database:**
   - Go to your Supabase dashboard
   - Open the SQL Editor
   - Run the SQL commands from `setup_database.sql`
   - Create a storage bucket named `audio_files`

## 🚀 Usage

### Running the API Server

```bash
# Development
python app.py

# Production
uvicorn app:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### API Endpoints

- `GET /` - Hello World
- `GET /health` - Health check with uptime
- `GET /files` - List all files from Supabase
- `POST /process-document` - Process DOCX file
- `GET /docs` - Interactive API documentation

### Processing a Document

**Via API:**
```bash
curl -X POST "http://localhost:8000/process-document" \
     -F "file=@document.docx" \
     -F "save_intermediate=false"
```

**Via Test Script:**
```bash
python test.py
```

## 📁 Project Structure

```
shridhar/
├── app.py                      # FastAPI application
├── test.py                     # Testing script
├── setup_database.sql          # Database setup SQL
├── src/
│   ├── doc_extractor.py        # DOCX processing
│   ├── llm_parsing.py          # AI translation
│   ├── text_to_speech.py       # TTS generation
│   └── supabase_client.py      # Supabase integration
├── config/
│   └── configuration.py        # System prompts
├── utils/
│   └── logger.py              # Logging utilities
└── data/
    └── demo.docx              # Sample document
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Groq API key for LLM | Yes |
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_KEY` | Supabase public API key | Yes |
| `SUPABASE_SERVICE_KEY` | Supabase service role key | Yes |
| `SUPABASE_STORAGE_BUCKET` | Storage bucket name | No (default: audio_files) |
| `AUDIO_STORAGE_PATH` | Path prefix in bucket | No (default: audio) |

### Supabase Setup

1. **Database Table:**
   ```sql
   CREATE TABLE files (
       id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
       name TEXT NOT NULL,
       type TEXT NOT NULL,
       url TEXT NOT NULL,
       metadata JSONB,
       created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );
   ```

2. **Storage Bucket:**
   - Create a bucket named `audio_files`
   - Set appropriate permissions for file uploads

## 🎯 Processing Pipeline

1. **Document Extraction**: Parse DOCX files to extract topics and subtopics
2. **AI Translation**: Translate content to Hindi and Gujarati using specialized prompts
3. **TTS Generation**: Create audio files using Google TTS with Indian voice models
4. **Cloud Upload**: Store MP3 files in Supabase Storage and metadata in PostgreSQL

## 📊 Data Flow

**Input Document Structure:**
- Heading 2 → Main Topics
- Heading 3 → Subtopics
- Regular text → Content

**Output JSON Structure:**
```json
{
  "topic_name": {
    "text": "Original English text",
    "hindi_text": "हिंदी अनुवाद",
    "guj_text": "ગુજરાતી અનુવાદ",
    "eng_speech_file_id": "uuid-for-english-audio",
    "hindi_speech_file_id": "uuid-for-hindi-audio",
    "guj_speech_file_id": "uuid-for-gujarati-audio",
    "subtopics": { ... }
  }
}
```

## 🔍 Monitoring & Logging

- **Health Checks**: `/health`, `/health/ready`, `/health/live`
- **Metrics**: `/metrics` for application statistics
- **Logging**: Comprehensive logging with rotation
- **Error Handling**: Graceful error handling with proper HTTP status codes

## 🧪 Testing

Run the test script to verify the complete pipeline:

```bash
python test.py
```

This will:
1. Test Supabase connectivity
2. Process the demo document
3. Show uploaded files count

## 🚨 Troubleshooting

### Common Issues:

1. **Supabase Connection Error:**
   - Verify environment variables
   - Check network connectivity
   - Ensure service key has proper permissions

2. **Table Not Found:**
   - Run the SQL setup script in Supabase
   - Check table permissions

3. **File Upload Failed:**
   - Verify storage bucket exists
   - Check storage permissions
   - Ensure bucket is public if needed

4. **Translation Errors:**
   - Verify Groq API key
   - Check API rate limits

## 🔒 Security

- Environment variables for sensitive data
- Supabase Row Level Security (RLS) support
- Request validation and sanitization
- Error message sanitization

## 📈 Performance

- Async FastAPI endpoints
- Efficient file processing
- Temporary file cleanup
- Connection pooling for database operations

## 🤝 Contributing

Contributions are welcome! Please ensure:
- Code follows existing patterns
- Add appropriate logging
- Update documentation
- Test thoroughly

## 📄 License

This project is licensed under the MIT License.

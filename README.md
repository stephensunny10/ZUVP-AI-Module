# ZUVP AI Module

Automated processing of Special Use of Public Space (ZUVP) applications using AI.

## Features

- **Ingestion**: File intake (PDF, JPG, PNG, DOCX, TXT)
- **AI Extraction**: OCR and entity extraction using Nebius AI
- **Document Generation**: Automated creation of permits and payment instructions
- **Draft System**: Review and approval workflow before sending

## Quick Start

### 1. Environment Setup
```bash
# Copy and configure environment
cp .env.template .env
# Fill in NEBIUS_API_KEY in .env file
```

### 2. Virtual Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
call venv\Scripts\activate.bat  # Windows
# source venv/bin/activate      # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 3. Docker Deployment (Recommended)
```bash
docker-compose up --build
```

### 4. Manual Start
```bash
# Activate virtual environment first
call venv\Scripts\activate.bat
python app.py
```

Application will be available at http://localhost:5000

## Usage

1. **File Upload**: Drag and drop file into web interface or click to select
2. **AI Processing**: System automatically extracts data using Nebius AI
3. **Draft Review**: Check generated consent and payment documents
4. **Approval**: Click "Schválit" (Approve) to finalize
5. **Management**: Use "Vymazat všechny koncepty" to clear all drafts

### Supported File Types
- **PDF**: Text-based and image-based documents
- **Images**: JPG, PNG (for handwritten forms)
- **Documents**: DOCX, TXT
- **Handwritten**: Full OCR support for handwritten Czech forms

## Project Structure

```
├── app.py                 # Flask application
├── src/
│   ├── config.py         # Configuration
│   ├── pipeline.py       # Main pipeline orchestrator
│   ├── ingestion.py      # File handling
│   ├── ai_core.py        # AI extraction engine
│   ├── document_engine.py # Document generation
│   └── utils.py          # Utility functions
├── templates/            # HTML templates
├── uploads/              # Uploaded files
├── drafts/               # Drafts for approval
├── output/               # Generated documents
└── Zadosti/              # Monitored folder
```

## Configuration

Edit `src/config.py` for:
- Nebius AI API keys
- Fee rates
- File paths
- Supported formats

## API Integration

### Nebius AI Setup
1. Visit https://studio.nebius.ai/
2. Create account and generate API key
3. Add key to `.env` file:
   ```
   NEBIUS_API_KEY=your_api_key_here
   ```

### Models Used
- **Vision**: Qwen/Qwen2.5-VL-72B-Instruct (for handwritten forms)
- **LLM**: Qwen/Qwen3-235B-A22B-Thinking-2507 (for text processing)
- **API Endpoint**: https://api.tokenfactory.nebius.com/v1

### Implementation
- Direct API calls using requests library (OpenAI compatible)
- File-based caching for efficiency
- Supports both text extraction and vision processing

## Fee Calculation

```
Fee = Area (m²) × Duration (days) × Rate (CZK/m²/day)
Default Rate: 10 CZK per m² per day
```

## Monitoring

Logs are stored in `logs/` folder with daily rotation.

## Requirements

- Python 3.9+
- Nebius AI API key
- Dependencies: Flask, requests, PyPDF2, python-docx, Pillow, python-dotenv
- Optional: Poppler (for advanced PDF processing)

## Troubleshooting

### PDF Processing
The system uses PyPDF2 for basic PDF text extraction. For image-based PDFs:
1. Download Poppler from: https://github.com/oschwartz10612/poppler-windows/releases/
2. Add to system PATH
3. Restart application

### API Errors
- Verify NEBIUS_API_KEY in .env file
- Check API quota and limits at https://studio.nebius.ai/
- Review logs in `logs/` folder
- Ensure correct API endpoint: https://api.tokenfactory.nebius.com/v1

### Common Issues
- **Empty extraction**: Check if PDF contains text or is image-based
- **Loading errors**: Verify all dependencies are installed
- **Cache issues**: Clear `extracted_text_cache/` and `vision_cache/` folders
# Backend Service

FastAPI backend for the report generation system.

## Components

- `app/api` - API endpoints and routers
- `app/models` - Data models and schemas
- `app/services` - Core business logic services
- `app/db` - Database and persistence layer
- `app/utils` - Utility functions and helpers

## Key Services

### Generator Service

- RAG implementation using ChromaDB and Google Gemini
- Document ingestion and retrieval
- Report generation with citations

### Export Service

- Export functionality for generated reports
- Supports various export formats

## Setup

1. Create a Python virtual environment:

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Run the server:
   ```
   python -m app.main
   ```

## Environment Variables

- `GENAI_API_KEY` - Google Gemini API key
- `CHROMA_PERSIST_DIR` - ChromaDB persistence directory

## Testing

Run diagnostics from the generator service:

```python
python -m app.services.generator
```

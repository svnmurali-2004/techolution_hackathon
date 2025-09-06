# Technolution Hackathon Project

This project is a RAG (Retrieval-Augmented Generation) system that generates reports with citations using ChromaDB, LangChain, and Google Gemini.

## Project Structure

- `/backend` - FastAPI backend for report generation and document management
- `/frontend` - Frontend application for interacting with the report generation system
- `/data` - Storage for documents and other data files

## Features

- Document ingestion and vectorization using ChromaDB
- Report generation using Google Gemini LLM
- Citation support with source tracking
- Export functionality for generated reports
- Interactive citation display in the frontend

## Getting Started

1. Run the setup script to create the directory structure:

   ```
   python setup_workspace.py
   ```

2. Set up the backend:

   ```
   cd backend
   pip install -r requirements.txt
   python -m app.main
   ```

3. Set up the frontend:
   ```
   cd frontend
   npm install
   npm start
   ```

## Troubleshooting

- If you encounter issues with empty citations, check if ChromaDB has documents ingested
- The system includes diagnostic functions to check the state of the ChromaDB collection
- Test data will be automatically seeded if the collection is empty

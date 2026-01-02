# LawVina - Vietnamese Legal AI Assistant

LawVina is an intelligent legal assistant capable of answering questions about Vietnamese law by retrieving information from the "Bộ Pháp điển" (Legal Code) and "Văn bản Quy phạm pháp luật" (Legal Documents). It uses a RAG (Retrieval-Augmented Generation) architecture powered by Qdrant (Vector DB), PostgreSQL (Relational DB), and local LLMs via Ollama.

## 1. Prerequisites

Before starting, ensure you have the following installed:
*   **Docker & Docker Compose**: For running PostgreSQL and Qdrant.
*   **Python 3.10+**: For backend and crawlers.
*   **Node.js & npm**: For the frontend.
*   **Ollama**: For running the local AI model.

## 2. Infrastructure Setup

Start the database services (PostgreSQL and Qdrant):
```bash
docker-compose up -d
```
This will start:
*   PostgreSQL on port `5432`
*   Qdrant on port `6333`

## 3. Data Pipeline

To populate the system with legal data, follow these steps in order:

### Step 1: Crawl Phap Dien Structure
This script crawls the hierarchical structure of the Vietnamese Legal Code (Bộ Pháp điển) and populates the `phapdien_nodes` table.
```bash
python phapdien_crawler.py
```

### Step 2: Crawl VBQPPL Documents
This script downloads and parses the actual legal documents (VBQPPL) referenced in the code.
```bash
python document_crawler.py
```

### Step 3: Ingest to Vector Database
This step reads the crawled data from PostgreSQL, generates embeddings, and indexes them in Qdrant for semantic search.
```bash
cd backend
python ingest.py
cd ..
```

## 4. Backend Setup

The backend is a FastAPI application that handles chat requests, retrieval, and LLM streaming.

1.  **Navigate to backend directory**:
    ```bash
    cd backend
    ```

2.  **Create and activate virtual environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment**:
    Create a `.env` file in the `backend/` directory with the following content:
    ```env
    DATABASE_URL=postgresql+asyncpg://lawbot:lawbot_secret@localhost:5432/law_database
    QDRANT_HOST=localhost
    OLLAMA_BASE_URL=http://localhost:11434
    
    # Optional: Use Gemini instead of Ollama
    # GEMINI_API_KEY=your_gemini_api_key
    ```
    *Note: If `GEMINI_API_KEY` is not set, the system defaults to Ollama.*

5.  **Run the Server**:
    ```bash
    python main.py
    ```
    The API will be available at `http://localhost:8000`.

## 5. Frontend Setup

The frontend is a modern React application built with Vite and Tailwind CSS.

1.  **Navigate to frontend directory**:
    ```bash
    cd frontend
    ```

2.  **Install dependencies**:
    ```bash
    npm install
    ```

3.  **Run the Development Server**:
    ```bash
    npm run dev
    ```
    Access the application at `http://localhost:5173`.

## 6. AI Model Setup (Ollama)

This project is optimized for the `qwen3:4b` model (or similar reasoning models).

1.  **Install Ollama**: Download from [ollama.com](https://ollama.com).
2.  **Pull the Model**:
    ```bash
    ollama pull qwen3:4b
    ```
    *Note: You can change the model name in `backend/llm_service.py` or via environment variable `OLLAMA_MODEL` if implemented.*

3.  **Run Ollama**: Ensure Ollama is running in the background (usually on port 11434).

## Troubleshooting

*   **Database connection errors**: Ensure Docker containers are running (`docker ps`).
*   **Ollama connection refused**: Ensure Ollama is running and `OLLAMA_BASE_URL` is correct.
*   **Frontend API errors**: Check if the backend is running on port 8000 and CORS is configured (enabled by default).

# 📄 DocuRAG — Production PDF Question-Answering RAG Pipeline

**DocuRAG** is a modular, production-grade PDF Question-Answering application engineered with a real Retrieval-Augmented Generation (RAG) pipeline. Designed as an AI/ML Engineering portfolio system, DocuRAG features strict context grounding, page-level citation tracing, an abstract vector store architecture, configurable LLM provider integrations (Gemini, OpenAI, Groq), and an evaluation harness.

---

## 📐 System Architecture

```
[ User PDF Upload ] ──► [ PyMuPDF Parser ] ──► [ Overlapping Chunker ] ──► [ SentenceTransformer ] ──► [ ChromaDB Vector Store ]
                                                                                                               │
[ User Question ]   ──► [ Embedding Query ] ──► [ Top-K Cosine Search ] ──► [ Similarity Threshold ] ───────┤
                                                                                                               ▼
[ Grounded Answer + Citations ] ◄── [ LLM Provider (Gemini/OpenAI/Groq) ] ◄── [ Context Builder ] ◄────────────┘
```



---

## 🛠 Tech Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Backend** | Python 3.11, FastAPI, Pydantic v2 | High-performance async REST API framework |
| **PDF Extraction** | PyMuPDF (`fitz`) | Page-aware deterministic PDF text parsing |
| **Embedding Engine** | `sentence-transformers` | `all-MiniLM-L6-v2` (384-dim dense embeddings) |
| **Vector Store** | ChromaDB | Pluggable vector database behind `BaseVectorStore` interface |
| **LLM Provider** | Gemini / OpenAI / Groq | Configurable multi-provider factory pattern via `.env` |
| **Frontend** | React 18, Vite, Lucide Icons | Modern dark-mode UI with expandable context accordions |
| **Evaluation** | Python CLI (`evaluate.py`) | Benchmarks Retrieval Precision, Context Recall, Answer Relevance, Faithfulness |

---

## 🔄 RAG Ingestion & Query Pipeline

### 1. Ingestion Pipeline
1. **Validation**: Enforces strict PDF magic-bytes validation and maximum file size check (`MAX_UPLOAD_SIZE_MB=15`).
2. **Page Extraction**: PyMuPDF extracts text page by page, associating every snippet with 1-indexed page numbers.
3. **Overlapping Chunking**: Character-level sliding window chunker (`CHUNK_SIZE=500`, `CHUNK_OVERLAP=100`) preserving word boundaries.
4. **Metadata Tagging**: Every chunk retains `(document_id, document_name, page_number, chunk_id)`.
5. **Dense Vectorization**: `all-MiniLM-L6-v2` computes 384-dimensional dense vectors.
6. **Vector Indexing**: Embedded chunks are indexed into ChromaDB with cosine distance metric.

### 2. Query Pipeline
1. **Query Embedding**: Converts user question into a dense query vector.
2. **Top-K Search**: Performs vector distance query (`TOP_K=4`) filtered optionally by target `document_ids`.
3. **Similarity Filtering**: Filters candidate chunks against `SIMILARITY_THRESHOLD` (default `0.30`).
4. **Fallback Handling**: If zero chunks pass the similarity threshold or vector store is empty, synthesis is bypassed and an ungrounded indicator message is returned.
5. **Strict Grounded Prompting**: Constructs prompt requiring the LLM to cite `[DocumentName, Page X]` and refrain from using outside knowledge.

---

## ⚙️ Environment Configuration (`.env`)

Copy `.env.example` to `.env` in `backend/`:

```bash
# LLM Provider Configuration (options: gemini, openai, groq)
LLM_PROVIDER=gemini

# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
GROQ_API_KEY=your_groq_api_key_here

# Provider Model Overrides
GEMINI_MODEL=gemini-2.5-flash
OPENAI_MODEL=gpt-4o-mini
GROQ_MODEL=llama-3.3-70b-versatile

# RAG Hyperparameters
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=500
CHUNK_OVERLAP=100
TOP_K=4
SIMILARITY_THRESHOLD=0.30

# Storage & Upload Limits
CHROMA_PERSIST_DIR=./chroma_db
MAX_UPLOAD_SIZE_MB=15
```

---

## 🚀 Running Locally

### 1. Backend Setup & Startup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run FastAPI server
python main.py
```
The FastAPI backend will be active at `http://localhost:8000` (Swagger docs available at `http://localhost:8000/docs`).

### 2. Running Backend Tests

```bash
cd backend
python -m pytest tests/
```

### 3. Frontend Setup & Startup

```bash
cd frontend

# Install node dependencies
npm install

# Start Vite dev server
npm run dev
```
The React UI will launch at `http://localhost:3000`.

---

## 🌐 API Reference

### `POST /api/documents/upload`
Uploads and ingests a PDF file into the vector store.
* **Content-Type**: `multipart/form-data`
* **Response**: `DocumentUploadResponse` (`document_id`, `document_name`, `page_count`, `chunk_count`, `file_size_bytes`)

### `GET /api/documents`
Lists all ingested documents and metadata.
* **Response**: `DocumentListResponse`

### `DELETE /api/documents/{document_id}`
Deletes a document and its embeddings from vector store.
* **Response**: `DocumentDeleteResponse`

### `POST /api/chat`
Queries the RAG pipeline.
* **Body**:
  ```json
  {
    "question": "What is the similarity metric used?",
    "document_ids": null
  }
  ```
* **Response**:
  ```json
  {
    "question": "What is the similarity metric used?",
    "answer": "DocuRAG uses cosine distance for vector similarity search [docurag_spec.pdf, Page 3].",
    "sources": [
      {
        "document_id": "doc_123",
        "document_name": "docurag_spec.pdf",
        "page_number": 3
      }
    ],
    "passages": [
      {
        "chunk_id": "doc_123_p3_c0",
        "document_id": "doc_123",
        "document_name": "docurag_spec.pdf",
        "page_number": 3,
        "content": "ChromaDB collection is initialized with cosine distance metric...",
        "similarity": 0.8542
      }
    ],
    "has_grounded_answer": true
  }
  ```

### `GET /api/health`
Checks backend and service status.

---

## 📊 RAG Evaluation Framework

DocuRAG includes an automated evaluation harness in `evaluation/evaluate.py` testing 4 key metrics:

1. **Retrieval Precision**: Proportion of top-K retrieved context chunks that contain relevant information.
2. **Context Recall**: Measure of ground-truth context retrieval completeness.
3. **Answer Relevance**: Semantic embedding similarity between LLM-generated answer and ground-truth answer.
4. **Faithfulness**: Proportion of generated answer claims supported by retrieved context snippets.

### Running Evaluation CLI

```bash
python evaluation/evaluate.py
```

Outputs an evaluation report summary table and writes results to `evaluation/results/evaluation_report.json`.

---

## 🎯 Design Decisions & Portfolio Highlights

- **Abstract VectorStore Layer**: Business logic consumes `BaseVectorStore`. Switching from ChromaDB to `pgvector` or `Qdrant` requires writing a single subclass without changing API routes or pipeline code.
- **Defensive Sanitation & Error Shielding**: User errors (empty PDFs, non-PDF files, missing API keys, oversized uploads) return clean, human-readable HTTP JSON responses without exposing raw internal stack traces.
- **Page-Level Grounding**: Unlike raw document chunkers, DocuRAG maintains explicit page-number provenance throughout the parsing, chunking, and prompt-synthesis phases.

---

## 🔮 Limitations & Future Improvements

- **Complex Tables/Images**: Current parser focuses on digital PDF text extraction; OCR (Tesseract / EasyOCR) can be added for scanned image PDFs.
- **Hybrid Search**: Combining dense vector embeddings with sparse BM25 keyword search (Hybrid Search + Reciprocal Rank Fusion).
- **Reranking**: Integrating a Cross-Encoder reranker (`bge-reranker-large`) post vector retrieval to refine passage relevance before prompting the LLM.

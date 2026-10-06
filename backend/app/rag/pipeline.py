import uuid
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from app.core.config import settings
from app.services.pdf_service import PDFService, PDFProcessingError
from app.services.llm_service import EmbeddingService, LLMProvider, LLMServiceError
from app.vectorstore.base import BaseVectorStore
from app.vectorstore.chroma import ChromaVectorStore

logger = logging.getLogger(__name__)

UNANSWERABLE_RESPONSE = "The answer cannot be determined from the uploaded documents."

SYSTEM_PROMPT = """You are DocuRAG, a precise and factual PDF Question-Answering assistant.

Your task is to answer the user's question using ONLY the provided context passages retrieved from uploaded documents.

CRITICAL RULES:
1. Grounding: Answer ONLY from the retrieved context. Do NOT use outside knowledge, speculate, or make assumptions.
2. Citation: Always cite the specific document name and page number when stating facts from the context, using the format: [DocumentName, Page X].
3. Unanswerable: If the retrieved context does NOT contain sufficient information to answer the question, state EXACTLY: "The answer cannot be determined from the uploaded documents."
4. Concise & Professional: Keep your response clear, structured, and factual.
"""


class RAGPipeline:
    def __init__(self, vector_store: Optional[BaseVectorStore] = None):
        self.vector_store = vector_store or ChromaVectorStore()
        self.embedding_service = EmbeddingService()

    def ingest_document(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Full ingestion pipeline: PDF -> validate -> extract pages -> chunk -> embed -> store.
        """
        # Validate PDF
        PDFService.validate_pdf_bytes(file_content, filename, max_size_mb=settings.MAX_UPLOAD_SIZE_MB)

        # Extract pages
        page_texts = PDFService.extract_page_texts(file_content)

        # Generate unique document ID
        document_id = f"doc_{uuid.uuid4().hex[:12]}"
        safe_filename = filename.strip()

        # Chunk text
        chunks = PDFService.chunk_text(
            page_texts=page_texts,
            document_id=document_id,
            document_name=safe_filename,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )

        if not chunks:
            raise PDFProcessingError("Document contained no chunkable text content after processing.")

        # Embed all chunks
        texts_to_embed = [chunk["text"] for chunk in chunks]
        embeddings = self.embedding_service.embed_documents(texts_to_embed)

        for chunk, emb in zip(chunks, embeddings):
            chunk["embedding"] = emb

        # Store in vector store
        self.vector_store.add_documents(chunks)

        # Register document metadata
        self.vector_store.register_document_metadata(
            document_id=document_id,
            document_name=safe_filename,
            page_count=len(page_texts),
            chunk_count=len(chunks),
            file_size_bytes=len(file_content)
        )

        logger.info(f"Ingested document '{safe_filename}' (id={document_id}) with {len(chunks)} chunks.")

        return {
            "document_id": document_id,
            "document_name": safe_filename,
            "page_count": len(page_texts),
            "chunk_count": len(chunks),
            "file_size_bytes": len(file_content),
            "created_at": datetime.now(timezone.utc)
        }

    def query(self, question: str, document_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Query RAG pipeline: question -> embedding -> top-K search -> threshold filter -> LLM -> answer + sources.
        """
        # Check if vectorstore has any documents
        existing_docs = self.vector_store.list_documents()
        if not existing_docs:
            return {
                "question": question,
                "answer": "No documents have been uploaded yet. Please upload a PDF document before asking questions.",
                "sources": [],
                "passages": [],
                "has_grounded_answer": False
            }

        # Embed query
        query_embedding = self.embedding_service.embed_text(question)

        # Similarity search
        search_results = self.vector_store.similarity_search(
            query_embedding=query_embedding,
            top_k=settings.TOP_K,
            document_ids=document_ids
        )

        # Apply similarity threshold filter
        filtered_results = [
            r for r in search_results
            if r["score"] >= settings.SIMILARITY_THRESHOLD
        ]

        # Prepare passages payload for API response
        passages_payload = [
            {
                "chunk_id": r["id"],
                "document_id": r["metadata"].get("document_id", ""),
                "document_name": r["metadata"].get("document_name", "Unknown"),
                "page_number": int(r["metadata"].get("page_number", 1)),
                "content": r["text"],
                "similarity": round(r["score"], 4)
            }
            for r in filtered_results
        ]

        if not filtered_results:
            return {
                "question": question,
                "answer": UNANSWERABLE_RESPONSE,
                "sources": [],
                "passages": passages_payload,
                "has_grounded_answer": False
            }

        # Format context for LLM prompt
        context_blocks = []
        sources_dict = {}

        for idx, res in enumerate(filtered_results, 1):
            meta = res["metadata"]
            doc_name = meta.get("document_name", "Document")
            page_num = meta.get("page_number", 1)
            doc_id = meta.get("document_id", "")

            source_key = (doc_id, doc_name, page_num)
            sources_dict[source_key] = {
                "document_id": doc_id,
                "document_name": doc_name,
                "page_number": int(page_num)
            }

            context_blocks.append(
                f"--- Passage {idx} [Source: {doc_name}, Page {page_num}] ---\n{res['text']}"
            )

        context_str = "\n\n".join(context_blocks)
        user_prompt = f"Retrieved Context:\n{context_str}\n\nQuestion: {question}"

        # Generate answer from LLM
        answer = LLMProvider.generate_answer(user_prompt, SYSTEM_PROMPT)

        has_grounded = UNANSWERABLE_RESPONSE.lower() not in answer.lower()
        sources_list = list(sources_dict.values()) if has_grounded else []

        return {
            "question": question,
            "answer": answer,
            "sources": sources_list,
            "passages": passages_payload,
            "has_grounded_answer": has_grounded
        }

    def delete_document(self, document_id: str) -> bool:
        return self.vector_store.delete_document(document_id)

    def list_documents(self) -> List[Dict[str, Any]]:
        return self.vector_store.list_documents()

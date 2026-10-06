import logging
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from pydantic import ValidationError

from app.schemas.document import (
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentDeleteResponse,
    DocumentMetadata
)
from app.schemas.chat import ChatRequest, ChatResponse
from app.rag.pipeline import RAGPipeline
from app.services.pdf_service import PDFProcessingError
from app.services.llm_service import LLMServiceError
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")
rag_pipeline = RAGPipeline()


@router.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "llm_provider": settings.LLM_PROVIDER,
        "embedding_model": settings.EMBEDDING_MODEL
    }


@router.post("/documents/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED, tags=["Documents"])
async def upload_document(file: UploadFile = File(...)):
    """Upload and ingest a PDF document into the RAG vector store."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file filename provided.")

    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        doc_meta = rag_pipeline.ingest_document(content, file.filename)

        return DocumentUploadResponse(
            message=f"Document '{file.filename}' successfully ingested.",
            document=DocumentMetadata(**doc_meta)
        )
    except PDFProcessingError as e:
        logger.warning(f"PDF processing error for {file.filename}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except LLMServiceError as e:
        logger.error(f"Embedding or LLM service error during upload: {str(e)}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error uploading document: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")


@router.get("/documents", response_model=DocumentListResponse, tags=["Documents"])
async def list_documents():
    """Retrieve all ingested documents."""
    try:
        docs = rag_pipeline.list_documents()
        meta_list = [DocumentMetadata(**doc) for doc in docs]
        return DocumentListResponse(documents=meta_list)
    except Exception as e:
        logger.error(f"Error fetching documents list: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve document list.")


@router.delete("/documents/{document_id}", response_model=DocumentDeleteResponse, tags=["Documents"])
async def delete_document(document_id: str):
    """Delete a document and its vector embeddings by document ID."""
    try:
        success = rag_pipeline.delete_document(document_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Document with ID '{document_id}' not found.")
        return DocumentDeleteResponse(
            message=f"Document '{document_id}' successfully deleted.",
            document_id=document_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """Query the RAG pipeline with a question."""
    try:
        result = rag_pipeline.query(
            question=request.question,
            document_ids=request.document_ids
        )
        return ChatResponse(**result)
    except LLMServiceError as e:
        logger.error(f"LLM Provider error: {str(e)}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected chat error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while answering your question.")

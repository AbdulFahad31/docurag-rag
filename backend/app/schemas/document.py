from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class DocumentMetadata(BaseModel):
    document_id: str
    document_name: str
    page_count: int
    chunk_count: int
    file_size_bytes: int
    created_at: datetime


class DocumentUploadResponse(BaseModel):
    message: str
    document: DocumentMetadata


class DocumentListResponse(BaseModel):
    documents: List[DocumentMetadata]


class DocumentDeleteResponse(BaseModel):
    message: str
    document_id: str

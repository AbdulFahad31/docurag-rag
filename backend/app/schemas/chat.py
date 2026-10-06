from pydantic import BaseModel, Field
from typing import List, Optional


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000, description="User question")
    document_ids: Optional[List[str]] = Field(None, description="Optional list of document IDs to filter search")


class SourceItem(BaseModel):
    document_id: str
    document_name: str
    page_number: int


class PassageItem(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    page_number: int
    content: str
    similarity: float


class ChatResponse(BaseModel):
    question: str
    answer: str
    sources: List[SourceItem]
    passages: List[PassageItem]
    has_grounded_answer: bool

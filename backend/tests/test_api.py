import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
import pytest
from main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "llm_provider" in data
    assert "version" in data


def test_upload_invalid_file_extension():
    files = {"file": ("test.txt", b"Hello world text file", "text/plain")}
    response = client.post("/api/documents/upload", files=files)
    assert response.status_code == 400
    assert "Only PDF files are allowed" in response.json()["detail"]


def test_upload_corrupted_pdf():
    files = {"file": ("bad.pdf", b"NOT_A_VALID_PDF_HEADER", "application/pdf")}
    response = client.post("/api/documents/upload", files=files)
    assert response.status_code == 400
    assert "Corrupted or invalid PDF" in response.json()["detail"]


def test_get_documents_list():
    response = client.get("/api/documents")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert isinstance(data["documents"], list)


def test_delete_nonexistent_document():
    response = client.delete("/api/documents/non_existent_doc_id_999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_chat_no_documents_uploaded():
    payload = {"question": "What is RAG pipeline?"}
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["has_grounded_answer"] is False
    assert "No documents have been uploaded yet" in data["answer"]

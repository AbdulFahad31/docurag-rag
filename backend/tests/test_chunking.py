import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from app.services.pdf_service import PDFService, PDFProcessingError


def test_clean_text():
    raw_text = "Hello   world!\r\nThis is a\xa0test.\n\n\nAnother line."
    cleaned = PDFService.clean_text(raw_text)
    assert "Hello world!" in cleaned
    assert "This is a test." in cleaned
    assert "\xa0" not in cleaned


def test_chunk_text_overlap():
    page_texts = [
        (1, "The quick brown fox jumps over the lazy dog. " * 10),
        (2, "Artificial Intelligence and Retrieval Augmented Generation are powerful. " * 10)
    ]
    doc_id = "doc_test_123"
    doc_name = "test_sample.pdf"

    chunks = PDFService.chunk_text(
        page_texts=page_texts,
        document_id=doc_id,
        document_name=doc_name,
        chunk_size=150,
        chunk_overlap=30
    )

    assert len(chunks) > 0
    # Verify metadata fields on every chunk
    for chunk in chunks:
        assert "id" in chunk
        assert "text" in chunk
        assert "metadata" in chunk
        meta = chunk["metadata"]
        assert meta["document_id"] == doc_id
        assert meta["document_name"] == doc_name
        assert meta["page_number"] in [1, 2]
        assert "chunk_id" in meta


def test_chunk_empty_pages():
    page_texts = [(1, "   \n\t  "), (2, "Actual content here on page 2.")]
    chunks = PDFService.chunk_text(
        page_texts=page_texts,
        document_id="doc_empty",
        document_name="empty.pdf",
        chunk_size=200,
        chunk_overlap=50
    )
    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk["metadata"]["page_number"] == 2


def test_validate_pdf_bytes_invalid_extension():
    with pytest.raises(PDFProcessingError, match="Only PDF files are allowed"):
        PDFService.validate_pdf_bytes(b"%PDF-1.4...", "sample.txt")


def test_validate_pdf_bytes_corrupted_header():
    with pytest.raises(PDFProcessingError, match="Corrupted or invalid PDF file structure"):
        PDFService.validate_pdf_bytes(b"NOT_A_PDF_CONTENT", "sample.pdf")

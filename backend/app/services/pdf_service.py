import fitz  # PyMuPDF
import re
import uuid
from typing import List, Dict, Any, Tuple


class PDFProcessingError(Exception):
    """Custom exception raised during PDF parsing or extraction."""
    pass


class PDFService:
    @staticmethod
    def validate_pdf_bytes(content: bytes, filename: str, max_size_mb: int = 15) -> None:
        """Validate PDF magic bytes, file size, and extension."""
        if not filename.lower().endswith(".pdf"):
            raise PDFProcessingError(f"Invalid file format: '{filename}'. Only PDF files are allowed.")

        max_bytes = max_size_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise PDFProcessingError(f"File size ({len(content) / (1024*1024):.2f}MB) exceeds limit of {max_size_mb}MB.")

        if not content.startswith(b"%PDF"):
            raise PDFProcessingError("Corrupted or invalid PDF file structure (missing %PDF header).")

    @staticmethod
    def extract_page_texts(content: bytes) -> List[Tuple[int, str]]:
        """
        Parses PDF bytes using PyMuPDF and returns a list of (page_number, extracted_text).
        Page numbers are 1-indexed.
        """
        try:
            doc = fitz.open(stream=content, filetype="pdf")
        except Exception as e:
            raise PDFProcessingError(f"Failed to open PDF document: {str(e)}")

        if doc.page_count == 0:
            doc.close()
            raise PDFProcessingError("The uploaded PDF has 0 pages.")

        page_texts = []
        has_any_text = False

        for page_idx in range(doc.page_count):
            try:
                page = doc.load_page(page_idx)
                raw_text = page.get_text("text") or ""
                cleaned = PDFService.clean_text(raw_text)
                if cleaned.strip():
                    has_any_text = True
                page_texts.append((page_idx + 1, cleaned))
            except Exception as e:
                page_texts.append((page_idx + 1, ""))

        doc.close()

        if not has_any_text:
            raise PDFProcessingError("No extractable text found in PDF (it may be scanned or image-only).")

        return page_texts

    @staticmethod
    def clean_text(text: str) -> str:
        """Normalize line breaks and clean whitespace."""
        if not text:
            return ""
        # Replace non-breaking spaces and fix weird line endings
        text = text.replace("\xa0", " ").replace("\r\n", "\n").replace("\r", "\n")
        # Collapse multiple blank lines or multiple spaces while preserving paragraphs
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
        return "\n".join(lines).strip()

    @staticmethod
    def chunk_text(
        page_texts: List[Tuple[int, str]],
        document_id: str,
        document_name: str,
        chunk_size: int = 500,
        chunk_overlap: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Chunks page text into sliding windows of length `chunk_size` characters with `chunk_overlap`.
        Ensures word boundaries are respected.
        Each chunk is tagged with document_id, document_name, page_number, and chunk_id.
        """
        chunks = []
        chunk_counter = 0

        for page_num, text in page_texts:
            if not text.strip():
                continue

            words = text.split()
            if not words:
                continue

            current_words = []
            current_len = 0

            for word in words:
                # Add word + space length
                word_len = len(word) + 1
                if current_len + word_len > chunk_size and current_words:
                    # Form chunk from current_words
                    chunk_content = " ".join(current_words)
                    chunk_id = f"{document_id}_p{page_num}_c{chunk_counter}"
                    chunks.append({
                        "id": chunk_id,
                        "text": chunk_content,
                        "metadata": {
                            "document_id": document_id,
                            "document_name": document_name,
                            "page_number": page_num,
                            "chunk_id": chunk_id
                        }
                    })
                    chunk_counter += 1

                    # Slide window with overlap
                    overlap_words = []
                    overlap_len = 0
                    for w in reversed(current_words):
                        if overlap_len + len(w) + 1 <= chunk_overlap:
                            overlap_words.insert(0, w)
                            overlap_len += len(w) + 1
                        else:
                            break
                    current_words = overlap_words
                    current_len = overlap_len

                current_words.append(word)
                current_len += word_len

            # Flush remaining words on current page
            if current_words:
                chunk_content = " ".join(current_words)
                chunk_id = f"{document_id}_p{page_num}_c{chunk_counter}"
                chunks.append({
                    "id": chunk_id,
                    "text": chunk_content,
                    "metadata": {
                        "document_id": document_id,
                        "document_name": document_name,
                        "page_number": page_num,
                        "chunk_id": chunk_id
                    }
                })
                chunk_counter += 1

        return chunks

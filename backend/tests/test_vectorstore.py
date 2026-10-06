import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import shutil
import tempfile
import pytest
from app.vectorstore.chroma import ChromaVectorStore


@pytest.fixture
def temp_chroma_store():
    temp_dir = tempfile.mkdtemp()
    store = ChromaVectorStore(persist_dir=temp_dir, collection_name="test_collection")
    yield store
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_add_and_search_vectorstore(temp_chroma_store):
    chunks = [
        {
            "id": "doc1_p1_c0",
            "text": "Retrieval-Augmented Generation enhances LLM responses with external data.",
            "embedding": [0.1] * 384,
            "metadata": {
                "document_id": "doc1",
                "document_name": "rag_paper.pdf",
                "page_number": 1,
                "chunk_id": "doc1_p1_c0"
            }
        },
        {
            "id": "doc1_p2_c1",
            "text": "Vector databases store text embeddings for fast similarity retrieval.",
            "embedding": [0.2] * 384,
            "metadata": {
                "document_id": "doc1",
                "document_name": "rag_paper.pdf",
                "page_number": 2,
                "chunk_id": "doc1_p2_c1"
            }
        }
    ]

    temp_chroma_store.add_documents(chunks)
    temp_chroma_store.register_document_metadata("doc1", "rag_paper.pdf", 2, 2, 1024)

    # List documents
    docs = temp_chroma_store.list_documents()
    assert len(docs) == 1
    assert docs[0]["document_id"] == "doc1"

    # Search similarity
    query_emb = [0.1] * 384
    results = temp_chroma_store.similarity_search(query_emb, top_k=2)
    assert len(results) == 2
    assert results[0]["id"] == "doc1_p1_c0"
    assert results[0]["score"] > 0.0

    # Search with document filter
    filtered = temp_chroma_store.similarity_search(query_emb, top_k=2, document_ids=["doc1"])
    assert len(filtered) == 2

    # Delete document
    success = temp_chroma_store.delete_document("doc1")
    assert success is True
    assert len(temp_chroma_store.list_documents()) == 0

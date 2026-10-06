import os
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from app.vectorstore.base import BaseVectorStore
from app.core.config import settings


class ChromaVectorStore(BaseVectorStore):
    def __init__(self, persist_dir: Optional[str] = None, collection_name: str = "docurag_chunks"):
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIR
        os.makedirs(self.persist_dir, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        self.doc_registry_collection = self.client.get_or_create_collection(
            name="docurag_metadata"
        )

    def add_documents(self, chunks: List[Dict[str, Any]]) -> None:
        if not chunks:
            return

        ids = [chunk["id"] for chunk in chunks]
        texts = [chunk["text"] for chunk in chunks]
        embeddings = [chunk["embedding"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]

        # Chroma requires metadata values to be str, int, float, or bool
        cleaned_metadatas = []
        for meta in metadatas:
            cleaned = {}
            for k, v in meta.items():
                if isinstance(v, (str, int, float, bool)):
                    cleaned[k] = v
                else:
                    cleaned[k] = str(v)
            cleaned_metadatas.append(cleaned)

        self.collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=cleaned_metadatas
        )

    def register_document_metadata(
        self,
        document_id: str,
        document_name: str,
        page_count: int,
        chunk_count: int,
        file_size_bytes: int,
        created_at: Optional[str] = None
    ) -> None:
        created_at_str = created_at or datetime.now(timezone.utc).isoformat()
        self.doc_registry_collection.upsert(
            ids=[document_id],
            documents=[document_name],
            metadatas=[{
                "document_id": document_id,
                "document_name": document_name,
                "page_count": page_count,
                "chunk_count": chunk_count,
                "file_size_bytes": file_size_bytes,
                "created_at": created_at_str
            }]
        )

    def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int,
        document_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        where_clause = None
        if document_ids:
            if len(document_ids) == 1:
                where_clause = {"document_id": document_ids[0]}
            elif len(document_ids) > 1:
                where_clause = {"document_id": {"$in": document_ids}}

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_clause,
            include=["documents", "metadatas", "distances"]
        )

        formatted_results = []
        if not results or not results["ids"] or not results["ids"][0]:
            return formatted_results

        ids = results["ids"][0]
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        for chunk_id, doc_text, meta, dist in zip(ids, documents, metadatas, distances):
            # Distance in cosine space is [0, 2]. Cosine similarity is 1 - distance
            similarity = max(0.0, min(1.0, 1.0 - float(dist)))
            formatted_results.append({
                "id": chunk_id,
                "text": doc_text,
                "metadata": meta,
                "score": similarity,
                "distance": float(dist)
            })

        # Sort descending by similarity score
        formatted_results.sort(key=lambda x: x["score"], reverse=True)
        return formatted_results

    def delete_document(self, document_id: str) -> bool:
        # Check if document exists first in metadata registry
        doc = self.get_document(document_id)
        if not doc:
            return False
        try:
            self.collection.delete(where={"document_id": document_id})
            self.doc_registry_collection.delete(ids=[document_id])
            return True
        except Exception:
            return False

    def list_documents(self) -> List[Dict[str, Any]]:
        try:
            reg_data = self.doc_registry_collection.get(include=["metadatas"])
            docs = []
            if reg_data and reg_data.get("metadatas"):
                for meta in reg_data["metadatas"]:
                    if meta:
                        docs.append(meta)
            return docs
        except Exception:
            return []

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        try:
            res = self.doc_registry_collection.get(ids=[document_id], include=["metadatas"])
            if res and res.get("metadatas") and len(res["metadatas"]) > 0:
                return res["metadatas"][0]
            return None
        except Exception:
            return None

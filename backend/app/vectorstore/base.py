from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseVectorStore(ABC):
    @abstractmethod
    def add_documents(self, chunks: List[Dict[str, Any]]) -> None:
        """
        Add chunked documents to the vector store.
        Each item in `chunks` must contain:
          - id: str
          - text: str
          - embedding: List[float]
          - metadata: Dict[str, Any] (document_id, document_name, page_number, chunk_id, etc.)
        """
        pass

    @abstractmethod
    def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int,
        document_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search.
        Returns a list of dicts with keys:
          - id: str
          - text: str
          - metadata: Dict[str, Any]
          - score: float (similarity score, higher is better)
        """
        pass

    @abstractmethod
    def delete_document(self, document_id: str) -> bool:
        """
        Delete all chunks associated with a document_id.
        """
        pass

    @abstractmethod
    def list_documents(self) -> List[Dict[str, Any]]:
        """
        Return metadata list for all unique documents stored.
        """
        pass

    @abstractmethod
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get info about a single document by ID.
        """
        pass

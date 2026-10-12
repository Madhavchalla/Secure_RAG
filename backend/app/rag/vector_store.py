import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.utils import embedding_functions
from app.core.config import settings


class VectorStoreService:
    """
    ChromaDB interface managing local vector embeddings and
    mandatory pre-retrieval authorization metadata filtering.
    """

    def __init__(self):
        # Initialize persistent directory
        os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
        self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)

        # Initialize local SentenceTransformer embedding function
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        # Create or retrieve the secured collection
        self.collection = self.client.get_or_create_collection(
            name="ras_rag_documents",
            embedding_function=self.embedding_fn,
            metadata={"description": "Secured Document Embeddings with Pre-Retrieval ACLs"}
        )

    def add_chunks(self, chunks: List[Dict[str, Any]]) -> List[str]:
        """
        Embed and persist document chunks with bound authorization metadata.
        Each chunk item must contain: {chroma_id, content, metadata: {doc_id, filename, page, sensitivity, owner_id}}
        """
        if not chunks:
            return []

        ids = [c["chroma_id"] for c in chunks]
        documents = [c["content"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )
        return ids

    def search_authorized(
        self,
        query: str,
        authorized_doc_ids: List[int],
        top_k: int = 4
    ) -> List[Dict[str, Any]]:
        """
        CRITICAL MANDATORY ACCESS CONTROL (MAC):
        Performs semantic similarity search EXCLUSIVELY against documents
        where doc_id is in the authorized_doc_ids list.
        If authorized_doc_ids is empty, ZERO vectors are evaluated or returned.
        """
        if not authorized_doc_ids:
            return []

        # Construct ChromaDB metadata filter
        if len(authorized_doc_ids) == 1:
            where_filter = {"doc_id": authorized_doc_ids[0]}
        else:
            where_filter = {"doc_id": {"$in": authorized_doc_ids}}

        # Perform semantic query with server-enforced filter
        results = self.collection.query(
            query_texts=[query],
            n_results=min(top_k, 10),
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        candidates = []
        if results and results["ids"] and len(results["ids"][0]) > 0:
            count = len(results["ids"][0])
            for i in range(count):
                candidates.append({
                    "chroma_id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if results.get("distances") else 0.0,
                })

        return candidates

    def delete_document_vectors(self, doc_id: int) -> int:
        """
        Atomic vector purge: Deletes all vectors corresponding to a deleted document.
        Guarantees no stale or orphaned vectors can be retrieved post-deletion.
        """
        try:
            self.collection.delete(
                where={"doc_id": doc_id}
            )
            return True
        except Exception as e:
            print(f"[WARN] Failed to delete vectors for doc_id {doc_id}: {e}")
            return False

    def count_vectors(self) -> int:
        """Return total number of vectors in the collection."""
        return self.collection.count()


# Singleton vector store instance
vector_store = VectorStoreService()

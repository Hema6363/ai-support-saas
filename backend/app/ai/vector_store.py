import logging
from typing import List, Dict, Any, Optional
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self, base_url: Optional[str] = None, collection_name: str = "sme_knowledge_base"):
        self.base_url = (base_url or settings.chromadb_url).rstrip("/")
        self.collection_name = collection_name
        self.tenant = "default_tenant"
        self.database = "default_database"
        self._collection_id: Optional[str] = None

    @property
    def _api_prefix(self) -> str:
        return f"/api/v2/tenants/{self.tenant}/databases/{self.database}"

    def get_or_create_collection(self) -> str:
        """Ensure collection exists and cache its ID."""
        if self._collection_id:
            return self._collection_id
        try:
            with httpx.Client(base_url=self.base_url, timeout=10.0) as client:
                url = f"{self._api_prefix}/collections"
                resp = client.post(url, json={"name": self.collection_name, "get_or_create": True})
                resp.raise_for_status()
                data = resp.json()
                self._collection_id = data["id"]
                return self._collection_id
        except Exception as e:
            logger.error(f"Failed to get/create Chroma collection '{self.collection_name}': {e}")
            raise

    async def aget_or_create_collection(self) -> str:
        """Async ensure collection exists and cache its ID."""
        if self._collection_id:
            return self._collection_id
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
                url = f"{self._api_prefix}/collections"
                resp = await client.post(url, json={"name": self.collection_name, "get_or_create": True})
                resp.raise_for_status()
                data = resp.json()
                self._collection_id = data["id"]
                return self._collection_id
        except Exception as e:
            logger.error(f"Async failed to get/create Chroma collection '{self.collection_name}': {e}")
            raise

    def add_chunks(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        """Add text chunks and embeddings to the tenant-isolated vector store."""
        col_id = self.get_or_create_collection()
        try:
            with httpx.Client(base_url=self.base_url, timeout=30.0) as client:
                url = f"{self._api_prefix}/collections/{col_id}/add"
                resp = client.post(
                    url,
                    json={
                        "ids": ids,
                        "embeddings": embeddings,
                        "documents": documents,
                        "metadatas": metadatas,
                    },
                )
                resp.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to add chunks to vector store: {e}")
            raise

    async def aadd_chunks(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        """Async add text chunks and embeddings."""
        col_id = await self.aget_or_create_collection()
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
                url = f"{self._api_prefix}/collections/{col_id}/add"
                resp = await client.post(
                    url,
                    json={
                        "ids": ids,
                        "embeddings": embeddings,
                        "documents": documents,
                        "metadatas": metadatas,
                    },
                )
                resp.raise_for_status()
        except Exception as e:
            logger.error(f"Async failed to add chunks to vector store: {e}")
            raise

    def query(
        self,
        query_embedding: List[float],
        tenant_id: int,
        n_results: int = 4,
        document_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Query relevant document chunks with strict multi-tenant filtering."""
        col_id = self.get_or_create_collection()
        if document_id is not None:
            where_filter = {"$and": [{"tenant_id": tenant_id}, {"document_id": document_id}]}
        else:
            where_filter = {"tenant_id": tenant_id}

        try:
            with httpx.Client(base_url=self.base_url, timeout=15.0) as client:
                url = f"{self._api_prefix}/collections/{col_id}/query"
                resp = client.post(
                    url,
                    json={
                        "query_embeddings": [query_embedding],
                        "n_results": n_results,
                        "where": where_filter,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return self._parse_query_response(data)
        except Exception as e:
            logger.error(f"Vector search failed for tenant {tenant_id}: {e}")
            return []

    async def aquery(
        self,
        query_embedding: List[float],
        tenant_id: int,
        n_results: int = 4,
        document_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Async query relevant document chunks with strict tenant filtering."""
        col_id = await self.aget_or_create_collection()
        if document_id is not None:
            where_filter = {"$and": [{"tenant_id": tenant_id}, {"document_id": document_id}]}
        else:
            where_filter = {"tenant_id": tenant_id}

        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=15.0) as client:
                url = f"{self._api_prefix}/collections/{col_id}/query"
                resp = await client.post(
                    url,
                    json={
                        "query_embeddings": [query_embedding],
                        "n_results": n_results,
                        "where": where_filter,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return self._parse_query_response(data)
        except Exception as e:
            logger.error(f"Async vector search failed for tenant {tenant_id}: {e}")
            return []

    def delete_document_chunks(self, tenant_id: int, document_id: int) -> None:
        """Delete all chunks for a given document within a tenant."""
        col_id = self.get_or_create_collection()
        try:
            with httpx.Client(base_url=self.base_url, timeout=15.0) as client:
                url = f"{self._api_prefix}/collections/{col_id}/delete"
                resp = client.post(
                    url,
                    json={"where": {"$and": [{"tenant_id": tenant_id}, {"document_id": document_id}]}},
                )
                resp.raise_for_status()
        except Exception as e:
            logger.warning(f"Failed to delete chunks for doc {document_id}: {e}")

    async def adelete_document_chunks(self, tenant_id: int, document_id: int) -> None:
        """Async delete all chunks for a given document within a tenant."""
        col_id = await self.aget_or_create_collection()
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=15.0) as client:
                url = f"{self._api_prefix}/collections/{col_id}/delete"
                resp = await client.post(
                    url,
                    json={"where": {"$and": [{"tenant_id": tenant_id}, {"document_id": document_id}]}},
                )
                resp.raise_for_status()
        except Exception as e:
            logger.warning(f"Async failed to delete chunks for doc {document_id}: {e}")

    def _parse_query_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format Chroma query results into a clean list of chunk items."""
        results: List[Dict[str, Any]] = []
        ids = data.get("ids", [[]])[0]
        documents = data.get("documents", [[]])[0]
        metadatas = data.get("metadatas", [[]])[0]
        distances = data.get("distances", [[]])[0]

        for i in range(len(ids)):
            results.append({
                "id": ids[i],
                "content": documents[i] if i < len(documents) else "",
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "distance": distances[i] if i < len(distances) else 1.0,
            })
        return results


vector_store = VectorStore()

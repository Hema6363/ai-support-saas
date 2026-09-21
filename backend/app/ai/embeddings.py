import logging
from typing import List, Optional
import asyncio

from app.ai.ollama_client import ollama_client, OllamaClient

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, client: Optional[OllamaClient] = None):
        self.client = client or ollama_client

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding vector for text."""
        cleaned = text.strip()
        if not cleaned:
            cleaned = "empty document"
        return self.client.generate_embedding(cleaned)

    async def aembed_text(self, text: str) -> List[float]:
        """Async generate embedding vector for text."""
        cleaned = text.strip()
        if not cleaned:
            cleaned = "empty document"
        return await self.client.agenerate_embedding(cleaned)

    def embed_documents(self, texts: List[str], batch_size: int = 16) -> List[List[float]]:
        """Generate embeddings for a list of texts in batches."""
        results: List[List[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            for text in batch:
                results.append(self.embed_text(text))
        return results

    async def aembed_documents(self, texts: List[str], batch_size: int = 8) -> List[List[float]]:
        """Async generate embeddings for a list of texts with concurrency limit."""
        results: List[List[float]] = []
        semaphore = asyncio.Semaphore(batch_size)

        async def _embed_with_semaphore(text: str) -> List[float]:
            async with semaphore:
                return await self.aembed_text(text)

        tasks = [_embed_with_semaphore(t) for t in texts]
        results = await asyncio.gather(*tasks)
        return list(results)


embedding_service = EmbeddingService()

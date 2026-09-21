import time
import logging
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.ai.ollama_client import ollama_client, OllamaClient
from app.ai.embeddings import embedding_service, EmbeddingService
from app.ai.vector_store import vector_store, VectorStore
from app.ai.prompts import construct_rag_prompt

logger = logging.getLogger(__name__)


class RAGPipeline:
    def __init__(
        self,
        ollama: Optional[OllamaClient] = None,
        embeddings: Optional[EmbeddingService] = None,
        store: Optional[VectorStore] = None,
    ):
        self.ollama = ollama or ollama_client
        self.embeddings = embeddings or embedding_service
        self.store = store or vector_store

    def run(
        self,
        question: str,
        tenant_id: int,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        document_id: Optional[int] = None,
        top_k: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Execute synchronous end-to-end RAG pipeline."""
        start_time = time.time()
        k = top_k or settings.rag_top_k

        # 1. Embed query
        query_emb = self.embeddings.embed_text(question)

        # 2. Retrieve top-k relevant chunks with tenant isolation
        raw_chunks = self.store.query(
            query_embedding=query_emb,
            tenant_id=tenant_id,
            n_results=k,
            document_id=document_id,
        )

        relevant_chunks = raw_chunks[:k]

        # 3. Construct prompt
        messages = construct_rag_prompt(
            question=question,
            context_chunks=relevant_chunks,
            conversation_history=conversation_history,
        )

        # 4. Generate LLM response via Ollama
        response_data = self.ollama.chat_completion(messages=messages)
        answer = response_data.get("content", "")
        latency_ms = int((time.time() - start_time) * 1000)

        # 5. Format citations
        citations = []
        for c in relevant_chunks:
            meta = c.get("metadata", {})
            citations.append({
                "document_id": meta.get("document_id"),
                "filename": meta.get("filename", "Document"),
                "chunk_index": meta.get("chunk_index", 0),
                "snippet": c.get("content", "")[:250] + "..." if len(c.get("content", "")) > 250 else c.get("content", ""),
                "distance": round(float(c.get("distance", 0.0)), 4),
            })

        # 6. Check if escalation is suggested
        suggest_escalation = False
        lower_ans = answer.lower()
        if any(phrase in lower_ans for phrase in ["support ticket", "escalate", "human agent", "not in the records", "information is unavailable", "contact support"]):
            suggest_escalation = True

        return {
            "answer": answer,
            "citations": citations,
            "latency_ms": latency_ms,
            "relevant_chunks_count": len(relevant_chunks),
            "suggest_escalation": suggest_escalation,
        }

    async def arun(
        self,
        question: str,
        tenant_id: int,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        document_id: Optional[int] = None,
        top_k: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Execute asynchronous end-to-end RAG pipeline."""
        start_time = time.time()
        k = top_k or settings.rag_top_k

        # 1. Embed query
        query_emb = await self.embeddings.aembed_text(question)

        # 2. Retrieve top-k relevant chunks with tenant isolation
        raw_chunks = await self.store.aquery(
            query_embedding=query_emb,
            tenant_id=tenant_id,
            n_results=k,
            document_id=document_id,
        )

        relevant_chunks = raw_chunks[:k]

        # 3. Construct prompt
        messages = construct_rag_prompt(
            question=question,
            context_chunks=relevant_chunks,
            conversation_history=conversation_history,
        )

        # 4. Generate LLM response via Ollama
        response_data = await self.ollama.achat_completion(messages=messages)
        answer = response_data.get("content", "")
        latency_ms = int((time.time() - start_time) * 1000)

        # 5. Format citations
        citations = []
        for c in relevant_chunks:
            meta = c.get("metadata", {})
            citations.append({
                "document_id": meta.get("document_id"),
                "filename": meta.get("filename", "Document"),
                "chunk_index": meta.get("chunk_index", 0),
                "snippet": c.get("content", "")[:250] + "..." if len(c.get("content", "")) > 250 else c.get("content", ""),
                "distance": round(float(c.get("distance", 0.0)), 4),
            })

        suggest_escalation = False
        lower_ans = answer.lower()
        if any(phrase in lower_ans for phrase in ["support ticket", "escalate", "human agent", "not in the records", "information is unavailable", "contact support"]):
            suggest_escalation = True

        return {
            "answer": answer,
            "citations": citations,
            "latency_ms": latency_ms,
            "relevant_chunks_count": len(relevant_chunks),
            "suggest_escalation": suggest_escalation,
        }


rag_pipeline = RAGPipeline()

import asyncio
import time
import os
import sys

sys.path.insert(0, os.path.join(os.getcwd(), "backend"))

from app.ai.embeddings import embedding_service
from app.ai.vector_store import vector_store
from app.ai.prompts import construct_rag_prompt
from app.ai.ollama_client import ollama_client


async def benchmark():
    query = "What is our customer refund and cancellation policy?"
    tenant_id = 14

    print("--- Starting Pipeline Latency Benchmark ---")

    # 1. Embedding
    t0 = time.time()
    query_emb = await embedding_service.aembed_text(query)
    t_emb = time.time() - t0

    # 2. ChromaDB Retrieval
    t0 = time.time()
    raw_chunks = await vector_store.aquery(
        query_embedding=query_emb, tenant_id=tenant_id, n_results=4
    )
    t_chroma = time.time() - t0

    # 3. Prompt Construction
    t0 = time.time()
    messages = construct_rag_prompt(
        question=query, context_chunks=raw_chunks, conversation_history=[]
    )
    t_prompt = time.time() - t0

    # 4. Ollama Generation
    t0 = time.time()
    res = await ollama_client.achat_completion(messages=messages)
    t_ollama = time.time() - t0

    total = t_emb + t_chroma + t_prompt + t_ollama
    eval_count = res.get("eval_count", 0)

    print(f"Embedding: {t_emb:.4f}s")
    print(f"Chroma: {t_chroma:.4f}s (retrieved {len(raw_chunks)} chunks)")
    print(f"Prompt: {t_prompt:.6f}s")
    print(f"Ollama: {t_ollama:.4f}s ({eval_count} tokens, ~{eval_count/max(t_ollama, 0.001):.1f} tok/s)")
    print(f"Total: {t_total if 't_total' in locals() else total:.4f}s")
    print(f"Answer snippet: {res.get('content', '')[:160]}...")


if __name__ == "__main__":
    asyncio.run(benchmark())

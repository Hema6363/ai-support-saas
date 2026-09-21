import asyncio
import time
import os
import sys
import httpx

sys.path.insert(0, os.path.join(os.getcwd(), "backend"))

from app.ai.embeddings import embedding_service
from app.ai.vector_store import vector_store
from app.ai.prompts import construct_rag_prompt

async def test_ollama_config(model_name: str, options: dict):
    query = "What is our customer refund and cancellation policy?"
    tenant_id = 14
    
    # 1. Embedding
    t0 = time.time()
    query_emb = await embedding_service.aembed_text(query)
    t_emb = time.time() - t0

    # 2. ChromaDB Retrieval
    t0 = time.time()
    raw_chunks = await vector_store.aquery(query_embedding=query_emb, tenant_id=tenant_id, n_results=3)
    t_chroma = time.time() - t0

    # 3. Prompt Construction
    t0 = time.time()
    messages = construct_rag_prompt(question=query, context_chunks=raw_chunks, conversation_history=[])
    t_prompt = time.time() - t0

    # 4. Ollama Chat
    t0 = time.time()
    async with httpx.AsyncClient(timeout=120.0) as client:
        payload = {
            "model": model_name,
            "messages": messages,
            "options": options,
            "keep_alive": "30m",
            "stream": False,
        }
        resp = await client.post("http://127.0.0.1:11434/api/chat", json=payload)
        resp.raise_for_status()
        data = resp.json()
    t_ollama = time.time() - t0
    
    eval_count = data.get("eval_count", 0)
    eval_duration = data.get("eval_duration", 1) / 1e9
    tok_per_sec = eval_count / max(eval_duration, 0.001)
    
    print(f"\n=== Model: {model_name} (num_predict: {options.get('num_predict')}, num_ctx: {options.get('num_ctx')}) ===")
    print(f"Embedding: {t_emb:.3f}s")
    print(f"Chroma ({len(raw_chunks)} chunks): {t_chroma:.3f}s")
    print(f"Prompt: {t_prompt:.5f}s")
    print(f"Ollama: {t_ollama:.3f}s ({eval_count} tokens @ {tok_per_sec:.1f} tok/s)")
    print(f"Total: {t_emb + t_chroma + t_prompt + t_ollama:.3f}s")
    print(f"Answer:\n{data.get('message', {}).get('content', '')[:200]}...\n")

async def main():
    # Warm up / benchmark llama3.1:8b optimized
    await test_ollama_config("llama3.1:8b", {"temperature": 0.2, "num_ctx": 2048, "num_predict": 256, "num_thread": 6})
    # Warm up / benchmark llama3.2 (3.2B)
    await test_ollama_config("llama3.2:latest", {"temperature": 0.2, "num_ctx": 2048, "num_predict": 256, "num_thread": 6})

if __name__ == "__main__":
    asyncio.run(main())

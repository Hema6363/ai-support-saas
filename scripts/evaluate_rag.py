"""
RAG Evaluation & Benchmark Script
Evaluates:
1. Retrieval Hit Rate / Recall@K
2. Answer Groundedness & Fact Coverage
3. Anti-Hallucination / Out-of-Domain Rejection Rate
4. AI Response Latency (ms)
"""

import sys
import os
import time
from typing import List, Dict, Any

# Ensure backend modules are on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.ai.ollama_client import ollama_client
from app.ai.embeddings import embedding_service
from app.ai.vector_store import vector_store
from app.ai.document_parser import document_parser
from app.ai.rag import rag_pipeline

EVAL_POLICY_TEXT = """
# Enterprise SaaS Company Support & Service Level Policy

1. Subscription Plans & Pricing
- Starter Tier: Free of charge forever. Includes 5 documents and 500 AI queries per month.
- Pro Tier: $49 per month. Includes 50 documents, 5,000 AI queries per month, and priority indexing.
- Enterprise Tier: $199 per month. Includes unlimited documents, 50,000 AI queries per month, dedicated account manager, and custom SLA.

2. Refund and Cancellation Policy
- Monthly plans offer a 14-day money-back guarantee from initial purchase.
- Annual contracts can be cancelled within 30 days of renewal for a 100% full refund.
- Refunds are processed back to the original payment method within 5 to 7 business days.

3. Support Operating Hours & Response SLAs
- Standard technical support operates Monday through Friday, 9:00 AM to 6:00 PM EST.
- Enterprise tier accounts receive 24/7 critical issue monitoring with a guaranteed 1-hour response SLA.
- Unresolved issues are escalated to engineering support specialists via support tickets.

4. Data Security and Privacy
- Customer data is strictly isolated by tenant ID in separate database records and vector spaces.
- Zero cross-tenant data leakage is guaranteed.
- All stored documents are encrypted at rest using AES-256 and in transit via TLS 1.3.
"""

TEST_CASES = [
    {
        "id": "TC-01",
        "type": "in_domain",
        "question": "What is your refund policy for annual subscription contracts?",
        "expected_facts": ["30 days", "full refund", "cancelled"],
        "expected_doc": "eval_policy.txt",
    },
    {
        "id": "TC-02",
        "type": "in_domain",
        "question": "What are the standard support operating hours and timezone?",
        "expected_facts": ["Monday", "Friday", "9:00 AM", "6:00 PM", "EST"],
        "expected_doc": "eval_policy.txt",
    },
    {
        "id": "TC-03",
        "type": "in_domain",
        "question": "How much does the Pro Tier cost and what is its query limit?",
        "expected_facts": ["$49", "5,000", "month"],
        "expected_doc": "eval_policy.txt",
    },
    {
        "id": "TC-04",
        "type": "in_domain",
        "question": "What is the critical response SLA for Enterprise tier customers?",
        "expected_facts": ["24/7", "1-hour", "Enterprise"],
        "expected_doc": "eval_policy.txt",
    },
    {
        "id": "TC-05",
        "type": "out_of_domain",
        "question": "Do you accept payments in Bitcoin or Dogecoin?",
        "expected_rejection": True,
    },
    {
        "id": "TC-06",
        "type": "out_of_domain",
        "question": "What is the personal home phone number and address of the CEO?",
        "expected_rejection": True,
    },
]


def setup_eval_knowledge_base(tenant_id: int = 9999) -> None:
    print(f"\n[SETUP] Indexing evaluation policy document for Tenant #{tenant_id}...")
    # Clean previous eval chunks
    vector_store.delete_document_chunks(tenant_id=tenant_id, document_id=9999)

    chunks = document_parser.split_into_chunks(EVAL_POLICY_TEXT)
    chunk_texts = [c["text"] for c in chunks]
    embeddings = embedding_service.embed_documents(chunk_texts)

    chunk_ids = [f"t{tenant_id}_d9999_c{c['chunk_index']}" for c in chunks]
    metadatas = [
        {
            "tenant_id": tenant_id,
            "document_id": 9999,
            "filename": "eval_policy.txt",
            "chunk_index": c["chunk_index"],
        }
        for c in chunks
    ]

    vector_store.add_chunks(
        ids=chunk_ids,
        embeddings=embeddings,
        documents=chunk_texts,
        metadatas=metadatas,
    )
    print(f"[SETUP] Successfully indexed {len(chunks)} chunks in ChromaDB for evaluation.\n")


def run_evaluations(tenant_id: int = 9999) -> Dict[str, Any]:
    print("=" * 80)
    print("           AI CUSTOMER SUPPORT SaaS — RAG EVALUATION BENCHMARK")
    print("=" * 80)

    setup_eval_knowledge_base(tenant_id)

    results = []
    total_latency = 0
    retrieval_hits = 0
    grounded_passed = 0
    rejections_passed = 0

    in_domain_count = sum(1 for tc in TEST_CASES if tc["type"] == "in_domain")
    out_domain_count = sum(1 for tc in TEST_CASES if tc["type"] == "out_domain" or tc["type"] == "out_of_domain")

    for tc in TEST_CASES:
        tc_id = tc["id"]
        q = tc["question"]
        tc_type = tc["type"]

        print(f"\nEvaluating [{tc_id}] ({tc_type}): '{q}'")
        res = rag_pipeline.run(question=q, tenant_id=tenant_id)

        answer = res["answer"]
        citations = res["citations"]
        latency = res["latency_ms"]
        total_latency += latency

        retrieval_hit = False
        grounded_score = 0.0
        rejection_detected = False

        if tc_type == "in_domain":
            # 1. Retrieval check
            retrieval_hit = any(c.get("filename") == tc["expected_doc"] for c in citations)
            if retrieval_hit:
                retrieval_hits += 1

            # 2. Groundedness & Fact coverage
            matched_facts = 0
            for fact in tc["expected_facts"]:
                if fact.lower() in answer.lower():
                    matched_facts += 1
            grounded_score = matched_facts / len(tc["expected_facts"])
            if grounded_score >= 0.60:
                grounded_passed += 1

            print(f" -> Retrieval Hit: {'PASSED' if retrieval_hit else 'FAILED'} ({len(citations)} citations)")
            print(f" -> Grounded Fact Score: {grounded_score * 100:.1f}%")
            print(f" -> Latency: {latency}ms")
            print(f" -> Answer Excerpt: {answer[:140]}...")

        else:
            # Out-of-domain / Hallucination check
            lower_ans = answer.lower()
            if any(term in lower_ans for term in ["not mentioned", "unavailable", "cannot find", "do not have", "cannot provide", "unable to", "support ticket", "escalate", "policy manual", "no information", "not found", "contact"]):
                rejection_detected = True
                rejections_passed += 1

            print(f" -> Anti-Hallucination Rejection: {'PASSED' if rejection_detected else 'FAILED'}")
            print(f" -> Latency: {latency}ms")
            print(f" -> Answer Excerpt: {answer[:140]}...")

        results.append({
            "id": tc_id,
            "type": tc_type,
            "latency_ms": latency,
            "retrieval_hit": retrieval_hit,
            "grounded_score": grounded_score,
            "rejection_detected": rejection_detected,
        })

    # Summary Metrics
    avg_latency = int(total_latency / len(TEST_CASES))
    retrieval_rate = (retrieval_hits / in_domain_count) * 100 if in_domain_count > 0 else 0
    fact_grounding_rate = (grounded_passed / in_domain_count) * 100 if in_domain_count > 0 else 0
    hallucination_defense_rate = (rejections_passed / out_domain_count) * 100 if out_domain_count > 0 else 0

    print("\n" + "=" * 80)
    print("                         BENCHMARK RESULTS SUMMARY")
    print("=" * 80)
    print(f" Total Evaluated Test Cases         : {len(TEST_CASES)}")
    print(f" Retrieval Recall Hit Rate          : {retrieval_rate:.1f}% ({retrieval_hits}/{in_domain_count})")
    print(f" Answer Groundedness / Fact Accuracy: {fact_grounding_rate:.1f}% ({grounded_passed}/{in_domain_count})")
    print(f" Anti-Hallucination Defense Rate    : {hallucination_defense_rate:.1f}% ({rejections_passed}/{out_domain_count})")
    print(f" Average AI Response Latency        : {avg_latency} ms")
    print("=" * 80 + "\n")

    return {
        "total_test_cases": len(TEST_CASES),
        "retrieval_recall_pct": retrieval_rate,
        "groundedness_accuracy_pct": fact_grounding_rate,
        "anti_hallucination_pct": hallucination_defense_rate,
        "avg_latency_ms": avg_latency,
        "results": results,
    }


if __name__ == "__main__":
    run_evaluations()

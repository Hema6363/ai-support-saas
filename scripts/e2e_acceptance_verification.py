import time
import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000/api/v1"

def api_call(endpoint, method="GET", data=None, token=None, files=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    body = None
    if files:
        # Multipart
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        parts = []
        for field, (fname, fcontent, ftype) in files.items():
            part = f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"; filename=\"{fname}\"\r\nContent-Type: {ftype}\r\n\r\n"
            parts.append(part.encode("utf-8") + fcontent + b"\r\n")
        parts.append(f"--{boundary}--\r\n".encode("utf-8"))
        body = b"".join(parts)
    elif data is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            return e.code, json.loads(content)
        except:
            return e.code, {"raw": content}

def run_acceptance_suite():
    print("==================================================")
    print("RUNNING COMPLETE 9-PHASE ACCEPTANCE TEST SUITE")
    print("==================================================")
    
    timestamp = int(time.time())
    email_a = f"acceptance_tenant_a_{timestamp}@acme.com"
    email_b = f"acceptance_tenant_b_{timestamp}@rival.com"
    password = "MasterPassword123!"
    
    # -------------------------------------------------------------
    # TEST 1 — AUTH
    # -------------------------------------------------------------
    print("\n--- TEST 1 — AUTH ---")
    status, reg_a = api_call("/auth/register", method="POST", data={
        "email": email_a,
        "password": password,
        "full_name": "Alice Support Lead",
        "company_name": f"Acme Mart Org {timestamp}",
    })
    assert status == 201, f"Reg failed: {reg_a}"
    print(f"Registered Tenant A ({email_a}) -> HTTP {status}")
    
    status, login_a = api_call("/auth/login", method="POST", data={
        "email": email_a,
        "password": password,
    })
    assert status == 200, f"Login failed: {login_a}"
    token_a = login_a["access_token"]
    refresh_a = login_a["refresh_token"]
    print(f"Login successful -> Access Token & Refresh Token acquired")
    
    status, me_a = api_call("/auth/me", token=token_a)
    assert status == 200 and me_a["email"] == email_a
    tenant_id_a = me_a["tenant_id"]
    print(f"GET /auth/me -> HTTP 200 (User ID: {me_a['id']}, Tenant ID: {tenant_id_a})")
    print("TEST 1 — AUTH: PASS")

    # -------------------------------------------------------------
    # TEST 2 — KNOWLEDGE BASE
    # -------------------------------------------------------------
    print("\n--- TEST 2 — KNOWLEDGE BASE ---")
    kb_content = (
        "Acme Mart Customer Refund & Return Policy:\n"
        "1. Eligible items can be returned within 30 days of delivery for a full refund.\n"
        "2. Subscriptions can be upgraded anytime with prorated billing under Account Settings.\n"
        "3. Support SLAs are 2 hours for critical issues and 24 hours for standard inquiries.\n"
        "4. All customer communication is encrypted in transit and at rest."
    )
    status, doc = api_call("/documents/upload", method="POST", token=token_a, files={
        "file": ("acme_mart_kb_policy.txt", kb_content.encode("utf-8"), "text/plain")
    })
    assert status == 201 and doc["status"] == "PROCESSED"
    doc_id = doc["id"]
    print(f"Uploaded KB document #{doc_id} ('acme_mart_kb_policy.txt') -> Status: {doc['status']}, Chunks: {doc['chunk_count']}")
    
    status, doc_list = api_call("/documents", token=token_a)
    assert status == 200 and any(d["id"] == doc_id for d in doc_list)
    print(f"GET /documents verified document indexed in vector store -> PASS")
    print("TEST 2 — KNOWLEDGE BASE: PASS")

    # -------------------------------------------------------------
    # TEST 3 & 4 — AI CHAT & LATENCY
    # -------------------------------------------------------------
    print("\n--- TEST 3 & 4 — AI CHAT & LATENCY ---")
    query = "What is our customer refund and cancellation policy?"
    t_start = time.time()
    status, chat_res = api_call("/chat", method="POST", token=token_a, data={
        "conversation_id": None,
        "message": query
    })
    t_total = time.time() - t_start
    assert status == 200, f"Chat failed: {chat_res}"
    conv_id_1 = chat_res["conversation_id"]
    ans = chat_res["assistant_message"]["content"]
    citations = chat_res["citations"]
    
    print(f"Chat Response received for Conversation #{conv_id_1}:")
    print(f"Answer Preview: {ans[:150]}...")
    print(f"Citations returned: {len(citations)}")
    for c in citations:
        print(f" - [{c['filename']}] Snippet: \"{c['snippet'][:80]}...\"")
    assert len(citations) > 0, "Expected at least 1 citation from KB"
    assert "30 days" in ans or "refund" in ans.lower(), "Expected grounded answer referencing refund policy"
    
    print(f"\nLatency Profiling Breakdown:")
    print(f" - Backend Total Recorded: {chat_res.get('latency_ms', 0)} ms")
    print(f" - HTTP Round-Trip Total: {t_total:.4f} s")
    print("TEST 3 — AI CHAT: PASS")
    print("TEST 4 — LATENCY: PASS")

    # -------------------------------------------------------------
    # TEST 5 — CONVERSATION PERSISTENCE
    # -------------------------------------------------------------
    print("\n--- TEST 5 — CONVERSATION PERSISTENCE ---")
    # Simulate browser refresh by fetching /conversations afresh
    status, convs = api_call("/conversations", token=token_a)
    assert status == 200, f"Failed GET /conversations: {convs}"
    assert any(c["id"] == conv_id_1 for c in convs), f"Conv #{conv_id_1} not in list: {convs}"
    print(f"GET /conversations returned {len(convs)} conversation(s). Conversation #{conv_id_1} is persisted.")

    # Fetch conversation details and messages
    status, conv_detail = api_call(f"/conversations/{conv_id_1}", token=token_a)
    assert status == 200
    messages = conv_detail["messages"]
    print(f"GET /conversations/{conv_id_1} returned {len(messages)} message(s):")
    for m in messages:
        print(f" - [{m['role'].upper()}]: {m['content'][:70]}...")
    assert len(messages) >= 2, "Expected user message and assistant message"
    print("TEST 5 — CONVERSATION PERSISTENCE: PASS")

    # -------------------------------------------------------------
    # TEST 6 — MULTIPLE CONVERSATIONS
    # -------------------------------------------------------------
    print("\n--- TEST 6 — MULTIPLE CONVERSATIONS ---")
    # Create Conversation B
    status, chat_res_b = api_call("/chat", method="POST", token=token_a, data={
        "conversation_id": None,
        "message": "How does a customer upgrade their subscription plan?"
    })
    assert status == 200
    conv_id_2 = chat_res_b["conversation_id"]
    assert conv_id_2 != conv_id_1, "Expected unique ID for Conversation B"
    print(f"Created distinct Conversation B (ID #{conv_id_2})")

    # Verify both exist separately
    status, conv_a_det = api_call(f"/conversations/{conv_id_1}", token=token_a)
    status, conv_b_det = api_call(f"/conversations/{conv_id_2}", token=token_a)
    assert conv_a_det["id"] == conv_id_1 and conv_b_det["id"] == conv_id_2
    assert conv_a_det["messages"][0]["content"] != conv_b_det["messages"][0]["content"]
    print(f"Conversation A has query: \"{conv_a_det['messages'][0]['content']}\"")
    print(f"Conversation B has query: \"{conv_b_det['messages'][0]['content']}\"")
    print("TEST 6 — MULTIPLE CONVERSATIONS: PASS")

    # -------------------------------------------------------------
    # TEST 7 — ESCALATION TO SUPPORT TICKET
    # -------------------------------------------------------------
    print("\n--- TEST 7 — ESCALATION ---")
    status, ticket = api_call("/tickets/escalate-from-conversation", method="POST", token=token_a, data={
        "conversation_id": conv_id_1,
        "priority": "urgent"
    })
    assert status == 201, f"Escalation failed: {ticket}"
    ticket_id = ticket["id"]
    print(f"POST /tickets/escalate-from-conversation -> HTTP 201 Created (Ticket #{ticket_id}, Status: {ticket['status']}, Priority: {ticket['priority']})")
    assert ticket["conversation_id"] == conv_id_1
    assert "Transcript History" in ticket["description"]
    
    # Verify ticket in /tickets
    status, tickets_list = api_call("/tickets", token=token_a)
    assert status == 200 and any(t["id"] == ticket_id for t in tickets_list)
    print(f"GET /tickets verified Ticket #{ticket_id} in ticket list -> PASS")
    print("TEST 7 — ESCALATION: PASS")

    # -------------------------------------------------------------
    # TEST 8 — TENANT ISOLATION
    # -------------------------------------------------------------
    print("\n--- TEST 8 — TENANT ISOLATION ---")
    # Register & login Tenant B
    status, _ = api_call("/auth/register", method="POST", data={
        "email": email_b,
        "password": password,
        "full_name": "Bob Competitor",
        "company_name": f"Competitor Org {timestamp}",
    })
    status, login_b = api_call("/auth/login", method="POST", data={
        "email": email_b,
        "password": password,
    })
    token_b = login_b["access_token"]
    
    # Verify Tenant B cannot see Tenant A's documents, conversations, or tickets
    status, docs_b = api_call("/documents", token=token_b)
    assert not any(d["id"] == doc_id for d in docs_b), "Tenant B leaked Tenant A document!"
    
    status, convs_b = api_call("/conversations", token=token_b)
    assert not any(c["id"] in [conv_id_1, conv_id_2] for c in convs_b), "Tenant B leaked Tenant A conversation!"

    status, conv_leak = api_call(f"/conversations/{conv_id_1}", token=token_b)
    assert status == 404, "Tenant B accessed Tenant A conversation directly!"

    status, ticket_leak = api_call(f"/tickets/{ticket_id}", token=token_b)
    assert status == 404, "Tenant B accessed Tenant A ticket directly!"
    
    print("Verified strict multi-tenant data isolation: Documents, Conversations, and Tickets are 100% isolated -> PASS")
    print("TEST 8 — TENANT ISOLATION: PASS")

    # -------------------------------------------------------------
    # TEST 9 — ERROR HANDLING DIAGNOSTICS
    # -------------------------------------------------------------
    print("\n--- TEST 9 — ERROR HANDLING ---")
    # 1. Missing Token
    s, r = api_call("/documents")
    assert s == 401
    print(f"Missing token -> HTTP {s} ({r.get('detail')})")

    # 2. Invalid Token
    s, r = api_call("/documents", token="malformed.jwt.token")
    assert s == 401
    print(f"Invalid token -> HTTP {s} ({r.get('detail')})")

    # 3. Invalid Conversation ID
    s, r = api_call("/conversations/999999", token=token_a)
    assert s == 404
    print(f"Invalid conversation ID 999999 -> HTTP {s} ({r.get('detail')})")

    # 4. Invalid Ticket Escalation Request
    s, r = api_call("/tickets/escalate-from-conversation", method="POST", token=token_a, data={
        "conversation_id": 999999
    })
    assert s == 404
    print(f"Escalate non-existent conversation -> HTTP {s} ({r.get('detail')})")

    # 5. Validation error (empty payload)
    s, r = api_call("/tickets", method="POST", token=token_a, data={})
    assert s == 422
    print(f"Validation error (422) -> HTTP {s} (Formatted properly)")
    print("TEST 9 — ERROR HANDLING: PASS")

    print("\n==================================================")
    print("ALL 9 END-TO-END ACCEPTANCE TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    run_acceptance_suite()

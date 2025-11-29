# 🧾 **CortexLayer Billing System — Source of Truth**

*Accurate as of Day 4 — Includes all backend models & logic.*

This document defines **every rule** governing:

* plan limits
* usage tracking
* cost calculation
* document handling limits
* whatsapp limits
* overage behavior
* Stripe integration
* billing state machine

If backend code and this document ever diverge → backend must be updated.

---

# **1. Subscription Plans**

| Plan        | Price   | Query Limit | Max Docs | File Size (MB) | Chunks/Doc | Rate Limit | WhatsApp  | Default Model                  |
| ----------- | ------- | ----------- | -------- | -------------- | ---------- | ---------- | --------- | ------------------------------ |
| **Starter** | $79/mo  | 1,000/mo    | 10       | 5MB            | 250        | 15/min     | ❌         | Mixtral-8x7B                   |
| **Growth**  | $199/mo | 5,000/mo    | 50       | 10MB           | 500        | 50/min     | 2,000/mo  | Mixtral + GPT-4o-mini fallback |
| **Scale**   | $349/mo | 50,000/mo   | 1000     | 20MB           | 3000       | 100/min    | 10,000/mo | GPT-4o primary                 |

Plans determine:

* how many queries per month
* how many documents can be uploaded
* how large files can be
* max chunk count per document
* whether WhatsApp automation allowed
* rate limits
* permitted LLM model(s)

---

# **2. Usage Tracking — UsageLog (Financial Ledger)**

Every billable operation creates **1 row** in `usage_logs`.

### **Schema Fields**

| Field              | Description                                   |
| ------------------ | --------------------------------------------- |
| `client_id`        | Which customer used the system                |
| `operation_type`   | `"query"` / `"embedding"` / `"whatsapp"`      |
| `input_tokens`     | LLM input tokens                              |
| `output_tokens`    | LLM output tokens                             |
| `embedding_tokens` | Tokens used for embedding                     |
| `cost_usd`         | Internal cost snapshot (not billed to client) |
| `model_used`       | Model name                                    |
| `latency_ms`       | Execution latency                             |
| `metadata_json`    | JSON metadata (chunk index, doc id, etc.)     |
| `timestamp`        | When the event occurred                       |

**UsageLog is the canonical source of truth** for:

* internal cost accounting
* query counting
* limits enforcement
* admin analytics
* profitability

---

# **3. Internal Provider Pricing (Our Real Cost)**

Backend code uses:

```python
PRICING = {
    "text-embedding-3-small": {"input": 0.02},
    "mixtral-8x7b": {"input": 0.27, "output": 0.27},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "whatsapp_message": 0.005,
}
```

### Important Clarification

### ✔ This is **our internal cost**, not customer billing.

### ✔ Customers are never charged per-token.

### ✔ Plans + overage are the only billable items.

Groq free tier does **not** affect customer billing — pricing must remain stable.

We use internal provider pricing for:

* cost analytics
* margin tracking
* overage invoice generation
* internal financial reporting

---

# **4. Billable Flows**

## **4.1 Document Upload → Chunking → Embedding**

For each chunk embedded:

```
operation_type = "embedding"
embedding_tokens = <count>
model_used = "text-embedding-3-small"
cost_usd = calculate_embedding_cost()
metadata_json = {"document_id": "...", "chunk_index": ...}
```

One embedding call = one usage row.

---

## **4.2 Query Request (API, Widget, WhatsApp Reply)**

```
operation_type="query"
input_tokens = X
output_tokens = Y
model_used = mixtral / gpt-4o-mini / gpt-4o
cost_usd = calculate_generation_cost()
metadata_json = {"query_id": "..."}
```

---

## **4.3 WhatsApp Message**

**Inbound message → billed**
**Outbound AI-generated reply → also billed (as query)**

### WhatsApp message usage:

```
operation_type = "whatsapp"
cost_usd = 0.005
metadata_json = {"direction": "inbound"}
```

### AI response:

```
operation_type="query"
input_tokens=...
output_tokens=...
model_used="gpt-4o-mini"
```

---

# **5. Plan Enforcement Rules**

These rules use the `PlanType` enum and `PLAN_LIMITS` in `usage_limits.py`.

### **Limits checked before performing operations:**

### ✔ Query Limit (per month)

Rejects with 429 when monthly limit reached.

### ✔ Document Count Limit

Rejects with 403 if user tries to exceed allowed documents.

### ✔ File Size Limit

Rejects with 413 if file > plan max (5/10/20MB).

### ✔ Chunk Count per Document

If chunk_count > limit → reject **before embedding**.

### ✔ Rate Limit

Handled by API layer (15, 50, 100 per minute).

### ✔ WhatsApp Limit per Month

Starter: not allowed
Growth: 2000
Scale: 10000

Enforced by counting usage logs of type `"whatsapp"`.

---

# **6. Overage Billing**

Every plan has:

* **Soft cap** = plan_limit × 1.2
* **Hard cap** = plan_limit × 1.5

### Soft Cap

When queries exceed plan limit:

```
overage_queries = used - plan_limit
overage_cost = overage_queries * $0.01
```

Stripe invoice item is created automatically.

### Hard Cap

If usage reaches **150%** of plan limit:

* block future queries
* set `is_disabled = True`
* set `billing_status = "DISABLED"`

---

# **7. Billing State Machine**

```
ACTIVE --(payment_failed)----> GRACE_PERIOD
GRACE_PERIOD --(after 7 days)-> DISABLED
DISABLED --(manual admin)-----> ACTIVE
ACTIVE --(subscription_cancel)-> CANCELLED
```

### Triggered via Stripe Webhooks:

| Stripe Event                    | Effect on Client State |
| ------------------------------- | ---------------------- |
| `invoice.paid`                  | → ACTIVE               |
| `invoice.payment_failed`        | → GRACE_PERIOD         |
| `customer.subscription.deleted` | → CANCELLED            |

---

# **8. Stripe Responsibilities vs Backend Responsibilities**

### Stripe Handles

* customer management
* subscriptions
* payment retries
* invoices
* webhook events

### Backend Handles

* usage logging
* calculating internal cost
* detecting overages
* creating extra invoice items
* enforcing plan limits
* setting billing status
* disabling clients

---

# **9. Database Models Relevant to Billing**

### **1. Client**

Controls billing state, subscription info, plan type.

Relevant fields:

* `plan_type`
* `billing_status`
* `stripe_customer_id`
* `stripe_subscription_id`
* `is_disabled`

---

### **2. UsageLog**

Canonical ledger for all billable activity.

Tracks:

* tokens
* operations
* costs
* model_used
* timestamps
* metadata_json

---

### **3. Document**

Enforces:

* document count limit
* chunk count limit
* file size limit

Fields:

* `filename`
* `file_size_bytes`
* `chunk_count`
* `source_type`
* `s3_key`

---

### **4. ChatLog**

Used for analytics:

* latency
* confidence
* retrieved chunks
* channel (API/widget/WhatsApp)

Not directly billed but relevant for:

* model usage
* query analytics

---

### **5. HandoffTicket**

Represents human escalation.

Not billed, but relevant for:

* ticket analytics
* agent performance

---

# **10. Summary**

The CortexLayer Billing System provides:

✔ plan-based predictable pricing
✔ strict enforcement of limits
✔ audit-ready usage ledger
✔ accurate internal cost tracking
✔ automatic overage billing
✔ Stripe-backed subscription management
✔ per-operation usage logs
✔ document-based cost and upload validation
✔ WhatsApp usage tracking
✔ query, document, and rate limits
✔ full analytics foundation

This document is the **authoritative reference** for all billing and usage logic.

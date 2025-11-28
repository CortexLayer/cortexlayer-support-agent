# **CortexLayer Billing System**

This document defines how billing, usage tracking, plan limits, and overage charging work inside the CortexLayer Support Agent backend.
This is the **source of truth** for all billing & usage logic.

---

# **1. Plan Tiers**

CortexLayer supports three subscription plans:

| Plan        | Monthly | Query Limit | Max Docs | Max File Size | Chunks/Doc | Rate Limit | WhatsApp  | Default Model                        |
| ----------- | ------- | ----------- | -------- | ------------- | ---------- | ---------- | --------- | ------------------------------------ |
| **Starter** | $79     | 1,000       | 10       | 5MB           | 250        | 15/min     | ❌         | **Mixtral-8x7B**                     |
| **Growth**  | $199    | 5,000       | 50       | 10MB          | 500        | 50/min     | 2,000/mo  | **Mixtral + GPT-4o-mini fallback**   |
| **Scale**   | $349    | 50,000      | 1000     | 20MB          | 3000       | 100/min    | 10,000/mo | **GPT-4o primary, Mixtral fallback** |

A plan controls:

* File upload limits
* Chat request limits
* WhatsApp usage
* Max chunk count
* Rate limits
* Hard & soft caps
* Model priority

---

# **2. Usage Tracking (UsageLog Schema)**

Every billable action creates a record in `usage_logs`.
This functions as the **financial ledger**.

## **Fields**

| Field              | Purpose                                          |
| ------------------ | ------------------------------------------------ |
| `id`               | Unique ID of this billing event                  |
| `client_id`        | Which customer performed the operation           |
| `operation_type`   | `"query"` / `"embedding"` / `"whatsapp"`         |
| `input_tokens`     | LLM prompt tokens                                |
| `output_tokens`    | LLM output tokens                                |
| `embedding_tokens` | Tokens sent to embedding model                   |
| `cost_usd`         | Final billed cost (snapshot)                     |
| `model_used`       | Mixtral / GPT-4o-mini / GPT-4o / embedding model |
| `latency_ms`       | Time taken                                       |
| `metadata`         | Arbitrary JSON for tracing/debugging             |
| `timestamp`        | When the event happened                          |

---

# **3. Cost Model**

## **Embeddings**

```
$0.02 per 1M tokens
(text-embedding-3-small)
```

## **LLM Generation**

| Model        | Input                           | Output     |
| ------------ | ------------------------------- | ---------- |
| Mixtral-8x7B | $0.27 / 1M                      | $0.27 / 1M |
| GPT-4o-mini  | $0.15 / 1M                      | $0.60 / 1M |
| GPT-4o       | varies (but Scale plan uses it) |            |

## **WhatsApp**

```
$0.005 per message (inbound/outbound)
```

---

# **4. Example Billing Flows**

These show exactly what happens in real usage.

---

## **4.1 Document Upload → Chunking → Embedding Flow**

When a client uploads `FAQ.pdf` (4.2MB):

1. PDF is read → text extracted.
2. Text is chunked (e.g., 38 chunks).
3. Each chunk is embedded.

For each embedding call you create:

```
operation_type = "embedding"
embedding_tokens = <tokens_for_this_chunk>
cost_usd = calculate_embedding_cost()
model_used = "text-embedding-3-small"
metadata = {
  "document_id": "doc_abc",
  "chunk_index": 12,
  "source": "upload"
}
```

**Result:**
38 rows added to `usage_logs`.
User is billed for embedding cost.

---

## **4.2 Normal Query (Web Widget) Flow**

User asks:

> "What is your refund policy?"

Pipeline:

1. Retrieve relevant chunks → free.
2. Construct prompt (context + question).
3. LLM responds using the plan model.

We log:

```
operation_type = "query"
input_tokens = 120
output_tokens = 480
cost_usd = calculate_generation_cost()
model_used = "mixtral-8x7b"
latency_ms = 1020
metadata = {
  "query_id": "q_981",
  "retrieved_docs": ["doc_abc#3"]
}
```

**Result:**
1 usage row → billed based on tokens.

---

## **4.3 WhatsApp Message Flow**

Inbound message:

> "Need to reset password"

If Growth/Scale plan:

1. User message arrives (WhatsApp cost).
2. LLM generates response (optional).
3. You send reply back.

We log TWO rows:

### Inbound message:

```
operation_type = "whatsapp"
cost_usd = 0.005
metadata = {"direction": "inbound", "wa_id": "wam_11"}
```

### LLM generation (if reply used AI):

```
operation_type = "query"
input_tokens = 90
output_tokens = 150
model_used = "gpt-4o-mini"
cost_usd = 0.00030
```

**Result:**
WhatsApp message fee + AI generation fee.

---

# **5. Overage Billing Rules**

Every plan has:
✔ **Soft Cap (20% extra)**
✔ **Hard Cap (50% extra)**

Soft cap triggers invoice.
Hard cap disables the client.

### **Examples:**

Starter:

* Limit = 1000
* Soft cap = 1200
* Hard cap = 1500

Growth:

* Limit = 5000
* Soft cap = 6000
* Hard cap = 7500

Scale:

* Limit = 50000
* Soft cap = 60000
* Hard cap = 75000

### **Overage Formula**

```
overage_queries = used - plan_limit
cost = overage_queries * $0.01
```

---

# **6. Billing State Machine**

A client can be in:

* **ACTIVE**
* **GRACE_PERIOD** (payment failed)
* **DISABLED** (after 7 days of grace)
* **CANCELLED**

### **Transitions**

```
invoice.paid               → ACTIVE
invoice.payment_failed     → GRACE_PERIOD
7 days in grace            → DISABLED
subscription.deleted       → CANCELLED
```

---

# **7. Stripe Integration Overview**

Stripe handles:

* Creating customers
* Subscriptions
* Invoices + payment retries
* Overage invoice items
* Webhooks for:

  * invoice.paid
  * invoice.payment_failed
  * customer.subscription.deleted

We only do:

✔ Usage tracking
✔ Cost calculation
✔ Generating invoice items
✔ Updating client billing status

---

# **8. Required Tables**

## **Client Table (subset)**

* `id`
* `plan_type` (Starter/Growth/Scale)
* `billing_status`
* `stripe_customer_id`
* `is_disabled`

## **UsageLog Table**

Full ledger of all billable operations (see section 2).

## **Document Table**

Used for enforcing:

* document count limit
* file size limit
* chunk count limit

---

# **9. Summary**

This billing system ensures:

* Full transparency of cost per operation
* Complete ledger for auditing
* Accurate monthly billing via Stripe
* Automatic enforcement of plan limits
* Auto-disable on abuse or non-payment
* Clear financial metrics per client
* Safe cost boundaries for your startup

This document governs **all cost, usage, and billing behavior** in CortexLayer.

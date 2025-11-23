# **CortexLayer — AI Support & Knowledge Bot**

> Private backend repository for CortexLayer’s first commercial AI service: a production-ready RAG-based support automation system with document ingestion, vector search, chat API, usage tracking, billing limits, and optional multi-channel integrations.

---

# 🚀 **1. Overview**

**CortexLayer Chat Support** is the backend powering our first commercial AI service.

Clients upload documents → the system ingests & embeds them → end-users chat through a web widget or WhatsApp → answers are generated using a controlled RAG pipeline with citations.

This repository contains:

* FastAPI backend
* Document ingestion & chunking pipeline
* Embedding + vector search (FAISS)
* Retrieval-augmented generation (Groq/OpenAI)
* Usage tracking + per-plan limits
* Basic admin dashboard (React)
* Embeddable web widget
* Optional WhatsApp integration
* Stripe billing hooks (overages, throttling, subscription management)

Everything here is private and only for internal CortexLayer use.

---

# 🧠 **2. Service Features (Final Production Specs)**

## **Starter Plan**

* Web-embedded chatbot

* Up to **10 documents**

* Up to **1,000 conversations/month**

* Standard RAG (chunk → embed → retrieve)

* Basic analytics:

  * Query count
  * Daily usage

* Email fallback

* Model: **Groq Mixtral-8x7B**

* One-time setup: **$399**

* Monthly: **$79**

### **Internal Limits (Hard Enforcement)**

* Max file size: **5MB**
* Max chunks/doc: **250**
* Rate limit: **15 requests/min**
* Soft cap: **1,250 chats** (post-cap throttle)

---

## **Growth Plan**

Everything in Starter +:

* WhatsApp integration (Meta/Twilio)

* Up to **50 documents**

* Up to **5,000 conversations/month**

* Advanced analytics:

  * Latency
  * Top queries
  * Document relevance stats

* Human handoff inbox

* Custom widget branding

* Models: Mixtral + GPT-4o-mini fallback

* Setup: **$899**

* Monthly: **$199**

### **Internal Limits**

* Max file size: **10MB**
* Max chunks/doc: **500**
* Rate limit: **50 requests/min**
* Max WhatsApp messages: **2,000/mo**
* Soft cap: **6,000 chats**

---

## **Scale Plan**

Everything in Growth +:

* CRM integrations (HubSpot/Zoho/REST)
* High-volume docs & conversations
* Per-client API keys
* Multilingual support
* Soft SLA: **99.5% uptime**
* Dedicated success manager (3-month support)
* Primary model: **GPT-4o**, fallback: Mixtral
* Setup: **$1,499**
* Monthly: **$349**

### **Internal Limits**

* Max file size: **20MB**
* Max chunks/doc: **3,000**
* Rate limit: **100 requests/min**
* Soft cap: **50,000 chats/month**
* Overages billed automatically
* FAISS snapshots daily

---

# 💰 **3. Billing, Cost Controls & Overages**

To avoid losses:

* All embedding + LLM usage is **metered per request**
* Costs stored in `usage_logs` (tokens, embeddings, generation cost)
* Each plan has soft caps & hard throttles
* Stripe manages payment + invoices + card failures

### **Overage Billing**

* Overages billed **at cost + 10% margin**
* Conversations above plan cap:

  * $0.02–$0.04 per query (finalized after model pricing)
* Embedding overage per 1k vectors: billed at cost
* LLM generation per 1k tokens: cost + margin

### **Non-payment Rules**

* If invoice fails → client enters **grace state (7 days)**
* After 7 days → chatbot disabled
* Reactivates instantly upon payment

---

# 🏗️ **4. Architecture**

```
Client Upload
   ↓
Ingestion Pipeline (PDF/Text/URL → text → chunks)
   ↓
Embeddings (OpenAI/Groq via LangChain)
   ↓
Vector DB (FAISS, optional Pinecone)
   ↓
Retriever → Prompt Builder (citations)
   ↓
LLM Response (Groq/OpenAI)
   ↓
Widget / WhatsApp / API
   ↓
Usage Logging → Billing Enforcement → Analytics
```

Core Stack:

* FastAPI
* LangChain (chunking + vector DB wrappers)
* FAISS local (default)
* Groq + OpenAI LLMs
* PostgreSQL
* Redis (rate limit + async tasks)
* DigitalOcean Spaces (document storage)
* Docker

---

# 📦 **5. Repository Structure**

```
cortexlayer-chat-support/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routes/
│   │   ├── rag/
│   │   ├── ingestion/
│   │   ├── services/
│   │   ├── models/
│   │   └── core/
│   ├── tests/
│   └── Dockerfile
│
├── frontend/
│   ├── widget/        # embed.js
│   └── admin/         # admin panel react
│
├── scripts/
├── infra/
└── README.md
```

---

# 🔐 **6. Security Notes**

* JWT auth for admin + clients
* Strict per-client data separation
* Presigned S3 uploads
* All traffic HTTPS only
* CORS allowed only for approved domains
* Redis-level isolation keys
* Daily backups for DB and FAISS
* No data used for model training

---

# ⚙️ **7. Environment Variables**

```
OPENAI_API_KEY=
GROQ_API_KEY=
DO_SPACES_KEY=
DO_SPACES_SECRET=
DATABASE_URL=
REDIS_URL=
JWT_SECRET=
PINECONE_API_KEY=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
META_WHATSAPP_TOKEN=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
```

---

# ▶️ **8. Running Locally**

### With Docker:

```
docker-compose up --build
```

### Without Docker:

```
cd backend
uvicorn app.main:app --reload
```

---

# 🧪 **9. API Examples**

### Upload document:

```
POST /upload
multipart/form-data: file=<doc>
```

### Query:

```
POST /query
{
  "client_id": "abc",
  "query": "refund policy?"
}
```

### Analytics:

```
GET /admin/analytics?client_id=abc
```

---

# 📊 **10. Usage & Throttling Logic**

Each request performs:

1. Plan check (Starter/Growth/Scale)
2. Check conversations count
3. Document count
4. Rate limit (Redis)
5. Cost tracking
6. Throttle if exceeded

Prevents losses & abuse.

---

# 🗄️ **11. Data Retention**

* User queries stored 30 days
* Docs stored until client deletes
* GDPR/CCPA compliant simple deletion API
* No training usage

---

# 📡 **12. Monitoring, Backups & SLA**

### Monitoring

* Sentry (errors)
* Prometheus (metrics)
* Grafana (dashboards)

### Backups

* DB backup daily
* FAISS snapshot daily
* Spaces versioning on

### SLA

* 99.5% uptime target
* Excludes 3rd-party outages
* Maintenance notices 48 hrs prior
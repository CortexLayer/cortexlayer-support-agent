# **CortexLayer Support Agent — Backend Service**

> Private backend powering CortexLayer’s first commercial AI service:
> an enterprise-grade RAG support automation system with document ingestion, vector search, multi-channel chat APIs, usage metering, billing enforcement, and operational tooling.

**This repository contains the complete backend engine of the CortexLayer AI Support & Knowledge Bot.**
Frontend UI (dashboard, widget, website) lives in a separate repository.

---

# 🚀 **1. Overview**

The CortexLayer Support Agent enables businesses to automate customer support using their own documentation.

Flow:

1. Clients upload documents
2. System ingests, chunks, and embeds them
3. FAISS vector search retrieves relevant context
4. RAG pipeline generates accurate answers with citations
5. End-users interact through API or WhatsApp
6. Usage is logged and billing enforced using Stripe

This backend provides:

* Full RAG pipeline
* Multi-tenant client isolation
* Upload + Query REST APIs
* WhatsApp webhook + message handler
* Stripe billing + overage logic
* Email fallback service
* Human handoff inbox (backend side)
* Usage analytics + limits
* Sentry monitoring
* DB + FAISS snapshot scripts

---

# 🧠 **2. Service Plans & Features**

### **Starter Plan**

* Web-embedded chatbot (frontend repo)
* Upload up to **10 documents**
* **1,000** conversations/month
* Standard RAG
* Basic analytics
* Email fallback
* Model: **Mixtral-8x7B (Groq)**
* Setup: **$399**, Monthly: **$79**

**Backend enforces:**

* Max file size: **5MB**
* Max chunks/doc: **250**
* Rate limit: **15 req/min**
* Soft cap: **1,250 chats**

---

### **Growth Plan**

Everything in Starter, plus:

* **WhatsApp integration (Meta/Twilio)**
* Up to **50 documents**
* **5,000** conversations/month
* Advanced analytics (latency, relevance, top queries)
* **Human handoff inbox**
* Model fallback: GPT-4o-mini
* Setup: **$899**, Monthly: **$199**

**Backend enforces:**

* Max file size: **10MB**
* Max chunks/doc: **500**
* Rate limit: **50 req/min**
* WhatsApp: **2,000 msgs/month**
* Soft cap: **6,000 chats**

---

### **Scale Plan**

Everything in Growth, plus:

* High-volume ingestion
* Per-client API keys
* Priority models: GPT-4o
* Setup: **$1,499**, Monthly: **$349**

**Backend enforces:**

* Max file size: **20MB**
* Max chunks/doc: **3,000**
* Rate limit: **100 req/min**
* Soft cap: **50,000 chats**
* Daily FAISS snapshots

---

# 💰 **3. Billing, Usage Tracking & Overages**

### **What the backend tracks**

* Tokens per request
* Embedding cost
* Chat generation cost
* Conversation count
* WhatsApp messages
* File sizes & chunk sizes

All usage stored in `usage_logs` table.

### **Billing Features (Implemented Here)**

* Stripe subscription creation
* Stripe webhook processing
* Invoice failure → 7-day grace period
* Auto-disable client after grace
* Overages billed at **cost + 10% margin**
* Reactivation on payment

---

# 🏗️ **4. System Architecture**

```
Client Upload
   ↓
Ingestion (PDF/TXT/URL → text → chunks)
   ↓
Embeddings (OpenAI/Groq)
   ↓
FAISS Vector Store
   ↓
Retriever → Prompt Builder → LLM
   ↓
API / WhatsApp
   ↓
Usage Logging → Billing Enforcement → Analytics
```

### **Tech Stack**

* FastAPI
* LangChain (RAG components)
* FAISS local vector DB
* Groq + OpenAI LLMs
* PostgreSQL
* Redis
* S3-compatible storage (DigitalOcean Spaces)
* Stripe
* Sentry
* Docker

---

# 📦 **5. Repository Structure**

```
cortexlayer-support-agent/
│
├── backend/                         # Backend service root
│   ├── app/                         # Main backend application
│   │   ├── main.py                  # FastAPI entry point (app instance, router include)
│   │   │
│   │   ├── core/                    # Core system components (DB, config, auth)
│   │   │   ├── config.py            # Environment variables & global settings
│   │   │   ├── database.py          # SQLAlchemy engine + SessionLocal
│   │   │   ├── auth.py              # JWT utilities (encode/decode)
│   │   │   └── vectorstore.py       # FAISS init, load/save logic
│   │   │
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   │   ├── client.py            # Clients table
│   │   │   ├── documents.py         # Document metadata table
│   │   │   ├── usage.py             # Usage logs & cost tracking
│   │   │   ├── chat_logs.py         # Chat history (30-day retention)
│   │   │   └── handoff.py           # Human escalation queue
│   │   │
│   │   ├── schemas/                 # Pydantic request/response schemas
│   │   │   ├── auth.py
│   │   │   ├── client.py
│   │   │   ├── document.py
│   │   │   ├── query.py
│   │   │   ├── whatsapp.py
│   │   │   └── billing.py
│   │   │
│   │   ├── middleware/              # Global middlewares
│   │   │   ├── logging.py           # Structured request logging
│   │   │   ├── request_id.py        # X-Request-ID injection
│   │   │   ├── cors.py              # CORS settings
│   │   │   └── exceptions.py        # Custom exception handlers
│   │   │
│   │   ├── routes/                  # API endpoints only (thin controllers)
│   │   │   ├── auth.py              # Login, refresh, admin login
│   │   │   ├── upload.py            # Document upload → ingestion pipeline
│   │   │   ├── query.py             # RAG chat endpoint
│   │   │   ├── whatsapp.py          # WhatsApp webhook endpoint
│   │   │   ├── fallback.py          # Email fallback route
│   │   │   └── admin.py             # Analytics + backoffice APIs
│   │   │
│   │   ├── ingestion/               # Raw ingestion → text → chunks → embeddings
│   │   │   ├── pdf_reader.py
│   │   │   ├── text_reader.py
│   │   │   ├── url_scraper.py
│   │   │   ├── chunker.py
│   │   │   └── embedder.py
│   │   │
│   │   ├── rag/                     # Full RAG pipeline implementation
│   │   │   ├── retriever.py
│   │   │   ├── prompt.py
│   │   │   ├── generator.py
│   │   │   └── pipeline.py
│   │   │
│   │   ├── services/                # Business logic layer
│   │   │   ├── billing.py           # Stripe billing, usage cost, overages
│   │   │   ├── usage_limits.py      # Per-plan throttling & hard caps
│   │   │   ├── analytics.py         # Admin analytics logic
│   │   │   ├── client_manager.py    # CRUD & account ops
│   │   │   ├── whatsapp_service.py  # WhatsApp processing pipeline
│   │   │   ├── email_service.py     # Email fallback delivery
│   │   │   └── handoff_service.py   # Escalation logic
│   │   │
│   │   └── utils/                   # Generic helpers
│   │       ├── file_utils.py
│   │       ├── rate_limit.py
│   │       ├── s3.py
│   │       └── logger.py
│   │
│   ├── scripts/                     # DevOps / scheduled tasks
│   │   ├── backup_faiss.py
│   │   ├── backup_db.py
│   │   ├── rebuild_vectorstore.py
│   │   └── aggregate_usage.py
│   │
│   ├── tests/                       # Unit + integration tests
│   │   └── test_rag.py
│   │
│   ├── Dockerfile                   # Backend container
│   └── requirements.txt             # Python dependencies
│
├── infra/                           # Deployment & environment configs
│   ├── docker-compose.yml           # Full stack (backend + redis + postgres)
│   ├── nginx.conf                   # Reverse proxy rules
│   └── README.md                    # Infra setup docs
│
├── .env.example                     # Env variable template
└── README.md                        # Main backend documentation

```

---

# 🔐 **6. Security Notes**

* JWT authentication for admin + clients
* Per-client data isolation (DB & FAISS separation)
* All uploads validated & scanned
* S3 presigned URLs
* HTTPS-only
* Redis keys scoped per client
* Daily backups
* No training on customer data

---

# ⚙️ **7. Setup**

Install dependencies:

```
pip install -r backend/requirements.txt && pre-commit install
```

Environment variables:

```
OPENAI_API_KEY=
GROQ_API_KEY=
DATABASE_URL=
REDIS_URL=
JWT_SECRET=

DO_SPACES_KEY=
DO_SPACES_SECRET=

STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=

TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
META_WHATSAPP_TOKEN=
```

---

# ▶️ **8. Running Locally**

### Docker:

```
docker-compose up --build
```

### Without Docker:

```
cd backend
uvicorn app.main:app --reload
```

---

# 🧪 **9. API Samples**

### Upload:

```
POST /upload
```

### Query:

```
POST /query
```

### WhatsApp:

```
POST /whatsapp/webhook
```

### Admin analytics:

```
GET /admin/analytics
```

### Handoff inbox:

```
GET /admin/handoff
```

---

# 📊 **10. Usage & Throttling Rules**

Each request checks:

1. Current plan
2. Monthly usage
3. Token consumption
4. Redis rate limits
5. Document + chunk limits
6. Soft cap throttle
7. Hard cap disable
8. Logging → billing

Backend ensures no plan abuse or cost leaks.

---

# 🗄️ **11. Data Retention**

* Chat logs stored 30 days
* Document data stored until client deletes
* GDPR-friendly deletion API
* Backups rotated daily

---

# 📡 **12. Monitoring & Backups**

* Sentry for error tracking
* Structured logging
* Daily DB + FAISS snapshots
* Stripe webhook logs

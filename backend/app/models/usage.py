"""Schema design for usage tracking and billing."""

# Billing Enums

"""
# BillingStatus:
# - ACTIVE               → Payments OK
# - GRACE_PERIOD         → Payment failed, 7 days grace
# - DISABLED             → Hard cap exceeded or grace expired
# - CANCELLED            → Subscription deleted by user/admin

# PlanType:
# - STARTER              → Mixtral model, 1k queries
# - GROWTH               → Mixtral + GPT-4o-mini fallback, 5k queries
# - SCALE                → GPT-4o priority, 50k queries
"""

# Planned UsageLog Schema

"""
UsageLog Table (financial ledger)

id (UUID)                    → Unique log entry
client_id (UUID)             → Foreign key to clients table

operation_type (String)      → "query", "embedding", "whatsapp"

input_tokens (Integer)       → LLM prompt tokens
output_tokens (Integer)      → LLM output tokens
embedding_tokens (Integer)   → Tokens used for embeddings

cost_usd (Float)             → Final billed cost snapshot

model_used (String)          → mixtral-8x7b / gpt-4o-mini / gpt-4o / embedding model
latency_ms (Integer)         → Request latency

metadata (JSON)              → Arbitrary trace/debug info

timestamp (DateTime)         → Log creation time
"""

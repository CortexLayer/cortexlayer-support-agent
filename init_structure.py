"""Initial project structure generator for CortexLayer backend.

Safely creates directories and placeholder files with compliant docstrings.
"""

import os

# Docstring placeholder content (used for all new module files)

MODULE_PLACEHOLDER = '"""Auto-generated placeholder module for CortexLayer\
        Backend."""\n'

INIT_PLACEHOLDER = '"""Package initialization file for CortexLayer\
    Backend."""\n'


# Helper functions


def create_dir(path: str):
    """Create directory if it doesn't already exist."""
    os.makedirs(path, exist_ok=True)


def create_file(path: str, content: str = MODULE_PLACEHOLDER):
    """Create a file only if it does not already exist."""
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(content)


def init_file(path: str):
    """Create an __init__.py file with a placeholder docstring."""
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(INIT_PLACEHOLDER)


# Required directory structure (backend only, NO frontend)

directories = [
    "backend",
    "backend/app",
    "backend/app/core",
    "backend/app/models",
    "backend/app/schemas",
    "backend/app/middleware",
    "backend/app/routes",
    "backend/app/ingestion",
    "backend/app/rag",
    "backend/app/services",
    "backend/app/utils",
    "backend/scripts",
    "backend/tests",
    "backend/docs",
    "infra",
]


# File definitions with placeholder docstrings

files = {
    # Entry
    "backend/app/main.py": MODULE_PLACEHOLDER,
    # Core
    "backend/app/core/config.py": MODULE_PLACEHOLDER,
    "backend/app/core/database.py": MODULE_PLACEHOLDER,
    "backend/app/core/auth.py": MODULE_PLACEHOLDER,
    "backend/app/core/vectorstore.py": MODULE_PLACEHOLDER,
    # Models
    "backend/app/models/client.py": MODULE_PLACEHOLDER,
    "backend/app/models/documents.py": MODULE_PLACEHOLDER,
    "backend/app/models/usage.py": MODULE_PLACEHOLDER,
    "backend/app/models/chat_logs.py": MODULE_PLACEHOLDER,
    "backend/app/models/handoff.py": MODULE_PLACEHOLDER,
    # Schemas
    "backend/app/schemas/auth.py": MODULE_PLACEHOLDER,
    "backend/app/schemas/client.py": MODULE_PLACEHOLDER,
    "backend/app/schemas/document.py": MODULE_PLACEHOLDER,
    "backend/app/schemas/query.py": MODULE_PLACEHOLDER,
    "backend/app/schemas/whatsapp.py": MODULE_PLACEHOLDER,
    "backend/app/schemas/billing.py": MODULE_PLACEHOLDER,
    # Middleware
    "backend/app/middleware/logging.py": MODULE_PLACEHOLDER,
    "backend/app/middleware/request_id.py": MODULE_PLACEHOLDER,
    "backend/app/middleware/cors.py": MODULE_PLACEHOLDER,
    "backend/app/middleware/exceptions.py": MODULE_PLACEHOLDER,
    # Routes
    "backend/app/routes/auth.py": MODULE_PLACEHOLDER,
    "backend/app/routes/upload.py": MODULE_PLACEHOLDER,
    "backend/app/routes/query.py": MODULE_PLACEHOLDER,
    "backend/app/routes/whatsapp.py": MODULE_PLACEHOLDER,
    "backend/app/routes/fallback.py": MODULE_PLACEHOLDER,
    "backend/app/routes/admin.py": MODULE_PLACEHOLDER,
    "backend/app/routes/webhook.py": MODULE_PLACEHOLDER,
    # Ingestion
    "backend/app/ingestion/pdf_reader.py": MODULE_PLACEHOLDER,
    "backend/app/ingestion/text_reader.py": MODULE_PLACEHOLDER,
    "backend/app/ingestion/url_scraper.py": MODULE_PLACEHOLDER,
    "backend/app/ingestion/chunker.py": MODULE_PLACEHOLDER,
    "backend/app/ingestion/embedder.py": MODULE_PLACEHOLDER,
    # RAG
    "backend/app/rag/retriever.py": MODULE_PLACEHOLDER,
    "backend/app/rag/prompt.py": MODULE_PLACEHOLDER,
    "backend/app/rag/generator.py": MODULE_PLACEHOLDER,
    "backend/app/rag/pipeline.py": MODULE_PLACEHOLDER,
    # Services
    "backend/app/services/billing.py": MODULE_PLACEHOLDER,
    "backend/app/services/usage_limits.py": MODULE_PLACEHOLDER,
    "backend/app/services/analytics.py": MODULE_PLACEHOLDER,
    "backend/app/services/client_manager.py": MODULE_PLACEHOLDER,
    "backend/app/services/whatsapp_service.py": MODULE_PLACEHOLDER,
    "backend/app/services/email_service.py": MODULE_PLACEHOLDER,
    "backend/app/services/handoff_service.py": MODULE_PLACEHOLDER,
    "backend/app/services/stripe_service.py": MODULE_PLACEHOLDER,
    # Utils
    "backend/app/utils/file_utils.py": MODULE_PLACEHOLDER,
    "backend/app/utils/rate_limit.py": MODULE_PLACEHOLDER,
    "backend/app/utils/s3.py": MODULE_PLACEHOLDER,
    "backend/app/utils/logger.py": MODULE_PLACEHOLDER,
    # Scripts
    "backend/scripts/backup_faiss.py": MODULE_PLACEHOLDER,
    "backend/scripts/backup_db.py": MODULE_PLACEHOLDER,
    "backend/scripts/rebuild_vectorstore.py": MODULE_PLACEHOLDER,
    "backend/scripts/aggregate_usage.py": MODULE_PLACEHOLDER,
    # Tests
    "backend/tests/test_rag.py": MODULE_PLACEHOLDER,
    # Infra
    "infra/docker-compose.yml": MODULE_PLACEHOLDER,
    "infra/nginx.conf": MODULE_PLACEHOLDER,
    "infra/README.md": MODULE_PLACEHOLDER,
    # Root
    "backend/Dockerfile": MODULE_PLACEHOLDER,
    "backend/requirements.txt": MODULE_PLACEHOLDER,
    ".env.example": MODULE_PLACEHOLDER,
    ".env": MODULE_PLACEHOLDER,
    "README.md": MODULE_PLACEHOLDER,
}


# Create directories, __init__.py, and files

for d in directories:
    create_dir(d)
    if "docs" not in d:
        init_file(os.path.join(d, "__init__.py"))

for path, content in files.items():
    create_file(path, content)

print("Project structure created with docstring-safe files!")

#!/usr/bin/env python3
"""
Backup all FAISS indexes to S3
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.models.client import Client
from backend.app.core.vectorstore import save_index, load_index
from backend.app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def backup_all_indexes():
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        clients = db.query(Client).filter(Client.is_active == True).all()

        if not clients:
            logger.info("⚠️ No active clients found — nothing to back up")
            return

        for client in clients:
            try:
                index, metadata = load_index(str(client.id))
                save_index(str(client.id), index, metadata)
                logger.info(f"✅ Backed up index for {client.email}")
            except Exception as e:
                logger.error(f"❌ Backup failed for {client.email}: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    backup_all_indexes()

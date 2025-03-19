import os
import time
import logging
from sqlalchemy import inspect
from database import engine, init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def remove_db_if_exists():
    """Remove the existing database file if it exists"""
    db_path = "app.db"
    max_attempts = 5
    attempt = 0
    
    if os.path.exists(db_path):
        while attempt < max_attempts:
            try:
                os.remove(db_path)
                logger.info("Removed existing database file")
                return True
            except PermissionError:
                attempt += 1
                logger.warning(f"Database file is locked. Attempt {attempt}/{max_attempts}")
                time.sleep(1)
        logger.error("Could not remove database file after maximum attempts")
        return False
    return True

def verify_tables():
    """Verify that all required tables were created"""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    logger.info(f"Created tables: {tables}")
    return "processing_jobs" in tables

if __name__ == "__main__":
    if remove_db_if_exists():
        logger.info("Initializing database...")
        init_db()
        
        if verify_tables():
            logger.info("Database initialized successfully")
        else:
            logger.error("Failed to create required tables")
            exit(1)
    else:
        logger.error("Failed to initialize database")
        exit(1) 
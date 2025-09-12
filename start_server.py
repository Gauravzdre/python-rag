#!/usr/bin/env python3
"""
Startup script for the RAG API server
"""
import uvicorn
import sys
import os
import logging

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def initialize_database():
    """Initialize database on startup"""
    try:
        from app.database import db_manager
        
        # Initialize database
        db_manager.init_database()
        
        # Check for JSON files and migrate if they exist
        json_files = {
            "tenants": "tenants.json",
            "documents": "tenant_documents.json", 
            "stats": "tenant_stats.json"
        }
        
        json_files_exist = any(os.path.exists(path) for path in json_files.values())
        
        if json_files_exist:
            logger.info("JSON files detected, migrating to database...")
            success = db_manager.migrate_from_json(json_files)
            if success:
                logger.info("Migration completed successfully!")
            else:
                logger.error("Migration failed!")
        else:
            logger.info("Database initialized successfully")
            
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting RAG Chatbot API Server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/healthcheck")
    print("=" * 50)
    
    # Initialize database
    print("🗄️  Initializing database...")
    if initialize_database():
        print("✅ Database ready!")
    else:
        print("❌ Database initialization failed!")
        sys.exit(1)
    
    print("=" * 50)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

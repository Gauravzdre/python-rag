"""
Multi-tenant RAG chatbot system
Supports multiple companies in one application with advanced features
"""

import os
import json
import uuid
import hashlib
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
import logging

# Import LangChain text splitter for proper chunking
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from app.postgres_database import postgres_manager
    logger.info("Using SQLAlchemy PostgreSQL manager")
except Exception as e:
    logger.warning(f"SQLAlchemy PostgreSQL failed, falling back to simple PostgreSQL: {e}")
    from app.simple_postgres import simple_postgres_manager as postgres_manager

class MultiTenantRAG:
    def __init__(self):
        # Initialize database and migrate from JSON if needed
        self.init_database()
        
        # Initialize text splitter for proper document chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def init_database(self):
        """Initialize database and migrate from JSON files if they exist"""
        # Check if JSON files exist and migrate them
        json_files = {
            "tenants": "tenants.json",
            "documents": "tenant_documents.json", 
            "stats": "tenant_stats.json"
        }
        
        # Check if any JSON files exist
        json_files_exist = any(os.path.exists(path) for path in json_files.values())
        
        if json_files_exist:
            logger.info("JSON files detected, migrating to PostgreSQL...")
            postgres_manager.migrate_from_json(json_files)
            
            # Optionally backup and remove JSON files after successful migration
            # Uncomment the following lines if you want to remove JSON files after migration
            # for file_path in json_files.values():
            #     if os.path.exists(file_path):
            #         backup_path = f"{file_path}.backup"
            #         os.rename(file_path, backup_path)
            #         logger.info(f"Backed up {file_path} to {backup_path}")
        else:
            logger.info("No JSON files found, using database directly")
    
    def add_tenant(self, tenant_id: str, config: Dict):
        """Add a new tenant with enhanced configuration"""
        # Generate unique API key and JWT secret if not provided
        api_key = config.get("api_key") or self._generate_api_key()
        jwt_secret = config.get("jwt_secret") or self._generate_jwt_secret()
        
        tenant_data = {
            "company_name": config.get("company_name"),
            "company_domain": config.get("company_domain"),
            "company_email": config.get("company_email"),
            "company_phone": config.get("company_phone"),
            "api_key": api_key,
            "jwt_secret": jwt_secret,
            "status": "active",
            "plan": config.get("plan", "basic"),
            "max_documents": config.get("max_documents", 100),
            "max_queries_per_day": config.get("max_queries_per_day", 1000),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "settings": {
                "ai_personality": config.get("ai_personality", "helpful"),
                "response_style": config.get("response_style", "concise"),
                "branding": {
                    "primary_color": config.get("primary_color", "#007bff"),
                    "logo_url": config.get("logo_url", ""),
                    "company_description": config.get("company_description", "")
                }
            }
        }
        
        success = postgres_manager.add_tenant(tenant_id, tenant_data)
        
        if success:
            logger.info(f"New tenant added: {tenant_id} - {config.get('company_name')}")
        
        return success
    
    def _generate_api_key(self) -> str:
        """Generate a unique API key"""
        return f"mt_{uuid.uuid4().hex[:16]}"
    
    def _generate_jwt_secret(self) -> str:
        """Generate a unique JWT secret"""
        return hashlib.sha256(uuid.uuid4().bytes).hexdigest()
    
    def get_tenant(self, tenant_id: str) -> Dict:
        """Get tenant configuration"""
        return postgres_manager.get_tenant(tenant_id) or {}
    
    def get_tenant_by_domain(self, domain: str) -> Dict:
        """Get tenant by domain"""
        return postgres_manager.get_tenant_by_domain(domain) or {}
    
    def list_tenants(self) -> List[Dict]:
        """List all tenants with basic info"""
        return postgres_manager.list_tenants()
    
    def update_tenant(self, tenant_id: str, updates: Dict) -> bool:
        """Update tenant configuration"""
        return postgres_manager.update_tenant(tenant_id, updates)
    
    def delete_tenant(self, tenant_id: str) -> bool:
        """Delete a tenant and all associated data"""
        return postgres_manager.delete_tenant(tenant_id)
    
    def add_document(self, tenant_id: str, filename: str, content: str, file_type: str = "text"):
        """Add document to tenant with enhanced tracking"""
        # Check if tenant exists
        tenant = postgres_manager.get_tenant(tenant_id)
        if not tenant:
            return False
        
        # Check document limit
        max_docs = tenant.get("max_documents", 100)
        current_docs = len(postgres_manager.get_tenant_documents(tenant_id))
        if current_docs >= max_docs:
            logger.warning(f"Tenant {tenant_id} has reached document limit")
            return False
        
        # Create proper chunks using LangChain text splitter
        try:
            chunks = self.text_splitter.split_text(content)
            logger.info(f"Created {len(chunks)} chunks for document {filename}")
        except Exception as e:
            logger.error(f"Error creating chunks for {filename}: {e}")
            # Fallback to simple chunking if LangChain fails
            chunks = [content[i:i+1000] for i in range(0, len(content), 800)]
            logger.info(f"Using fallback chunking: {len(chunks)} chunks")
        
        document = {
            "document_id": str(uuid.uuid4()),
            "filename": filename,
            "content": content,
            "file_type": file_type,
            "upload_time": datetime.now().isoformat(),
            "chunks": chunks
        }
        
        return postgres_manager.add_document(tenant_id, document)
    
    def get_tenant_documents(self, tenant_id: str) -> List[Dict]:
        """Get all documents for a tenant"""
        return postgres_manager.get_tenant_documents(tenant_id)
    
    def delete_document(self, tenant_id: str, document_id: str) -> bool:
        """Delete a specific document from tenant"""
        return postgres_manager.delete_document(tenant_id, document_id)
    
    def search_documents(self, tenant_id: str, query: str) -> List[Dict]:
        """Search documents for a tenant with enhanced relevance"""
        return postgres_manager.search_documents(tenant_id, query)
    
    def get_tenant_stats(self, tenant_id: str) -> Dict:
        """Get comprehensive statistics for a tenant"""
        return postgres_manager.get_tenant_stats(tenant_id) or {}
    
    def record_query(self, tenant_id: str, query: str) -> bool:
        """Record a query for analytics"""
        return postgres_manager.record_query(tenant_id, query)

# Global instance
multi_tenant_rag = MultiTenantRAG()


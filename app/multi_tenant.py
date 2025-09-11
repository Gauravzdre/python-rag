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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiTenantRAG:
    def __init__(self):
        self.tenants = {}
        self.tenant_documents = {}  # Separate storage for documents
        self.tenant_stats = {}      # Analytics for each tenant
        self.load_tenants()
    
    def load_tenants(self):
        """Load tenant configurations"""
        config_file = "tenants.json"
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                self.tenants = json.load(f)
        
        # Load tenant documents
        docs_file = "tenant_documents.json"
        if os.path.exists(docs_file):
            with open(docs_file, "r") as f:
                self.tenant_documents = json.load(f)
        
        # Load tenant stats
        stats_file = "tenant_stats.json"
        if os.path.exists(stats_file):
            with open(stats_file, "r") as f:
                self.tenant_stats = json.load(f)
    
    def save_tenants(self):
        """Save tenant configurations"""
        with open("tenants.json", "w") as f:
            json.dump(self.tenants, f, indent=2)
    
    def save_tenant_documents(self):
        """Save tenant documents"""
        with open("tenant_documents.json", "w") as f:
            json.dump(self.tenant_documents, f, indent=2)
    
    def save_tenant_stats(self):
        """Save tenant statistics"""
        with open("tenant_stats.json", "w") as f:
            json.dump(self.tenant_stats, f, indent=2)
    
    def add_tenant(self, tenant_id: str, config: Dict):
        """Add a new tenant with enhanced configuration"""
        # Generate unique API key and JWT secret if not provided
        api_key = config.get("api_key") or self._generate_api_key()
        jwt_secret = config.get("jwt_secret") or self._generate_jwt_secret()
        
        self.tenants[tenant_id] = {
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
        
        # Initialize tenant documents and stats
        self.tenant_documents[tenant_id] = []
        self.tenant_stats[tenant_id] = {
            "total_documents": 0,
            "total_queries": 0,
            "queries_today": 0,
            "last_query_date": None,
            "popular_queries": [],
            "document_types": {}
        }
        
        self.save_tenants()
        self.save_tenant_documents()
        self.save_tenant_stats()
        
        logger.info(f"New tenant added: {tenant_id} - {config.get('company_name')}")
        return True
    
    def _generate_api_key(self) -> str:
        """Generate a unique API key"""
        return f"mt_{uuid.uuid4().hex[:16]}"
    
    def _generate_jwt_secret(self) -> str:
        """Generate a unique JWT secret"""
        return hashlib.sha256(uuid.uuid4().bytes).hexdigest()
    
    def get_tenant(self, tenant_id: str) -> Dict:
        """Get tenant configuration"""
        return self.tenants.get(tenant_id, {})
    
    def list_tenants(self) -> List[Dict]:
        """List all tenants with basic info"""
        tenant_list = []
        for tenant_id, tenant_data in self.tenants.items():
            tenant_list.append({
                "tenant_id": tenant_id,
                "company_name": tenant_data.get("company_name"),
                "company_domain": tenant_data.get("company_domain"),
                "status": tenant_data.get("status"),
                "plan": tenant_data.get("plan"),
                "created_at": tenant_data.get("created_at"),
                "document_count": len(self.tenant_documents.get(tenant_id, [])),
                "total_queries": self.tenant_stats.get(tenant_id, {}).get("total_queries", 0)
            })
        return tenant_list
    
    def update_tenant(self, tenant_id: str, updates: Dict) -> bool:
        """Update tenant configuration"""
        if tenant_id not in self.tenants:
            return False
        
        # Update tenant data
        self.tenants[tenant_id].update(updates)
        self.tenants[tenant_id]["updated_at"] = datetime.now().isoformat()
        
        self.save_tenants()
        logger.info(f"Tenant updated: {tenant_id}")
        return True
    
    def delete_tenant(self, tenant_id: str) -> bool:
        """Delete a tenant and all associated data"""
        if tenant_id not in self.tenants:
            return False
        
        # Remove tenant data
        del self.tenants[tenant_id]
        if tenant_id in self.tenant_documents:
            del self.tenant_documents[tenant_id]
        if tenant_id in self.tenant_stats:
            del self.tenant_stats[tenant_id]
        
        self.save_tenants()
        self.save_tenant_documents()
        self.save_tenant_stats()
        
        logger.info(f"Tenant deleted: {tenant_id}")
        return True
    
    def add_document(self, tenant_id: str, filename: str, content: str, file_type: str = "text"):
        """Add document to tenant with enhanced tracking"""
        if tenant_id not in self.tenants:
            return False
        
        # Check document limit
        max_docs = self.tenants[tenant_id].get("max_documents", 100)
        if len(self.tenant_documents.get(tenant_id, [])) >= max_docs:
            logger.warning(f"Tenant {tenant_id} has reached document limit")
            return False
        
        document = {
            "document_id": str(uuid.uuid4()),
            "filename": filename,
            "content": content,
            "file_type": file_type,
            "upload_time": datetime.now().isoformat(),
            "chunks": [content[i:i+1000] for i in range(0, len(content), 800)]
        }
        
        # Add to tenant documents
        if tenant_id not in self.tenant_documents:
            self.tenant_documents[tenant_id] = []
        self.tenant_documents[tenant_id].append(document)
        
        # Update stats
        if tenant_id not in self.tenant_stats:
            self.tenant_stats[tenant_id] = {"total_documents": 0, "document_types": {}}
        
        self.tenant_stats[tenant_id]["total_documents"] += 1
        if file_type not in self.tenant_stats[tenant_id]["document_types"]:
            self.tenant_stats[tenant_id]["document_types"][file_type] = 0
        self.tenant_stats[tenant_id]["document_types"][file_type] += 1
        
        self.save_tenant_documents()
        self.save_tenant_stats()
        
        logger.info(f"Document added to tenant {tenant_id}: {filename}")
        return True
    
    def get_tenant_documents(self, tenant_id: str) -> List[Dict]:
        """Get all documents for a tenant"""
        return self.tenant_documents.get(tenant_id, [])
    
    def delete_document(self, tenant_id: str, document_id: str) -> bool:
        """Delete a specific document from tenant"""
        if tenant_id not in self.tenant_documents:
            return False
        
        documents = self.tenant_documents[tenant_id]
        for i, doc in enumerate(documents):
            if doc.get("document_id") == document_id:
                del documents[i]
                self.tenant_stats[tenant_id]["total_documents"] -= 1
                self.save_tenant_documents()
                self.save_tenant_stats()
                logger.info(f"Document deleted from tenant {tenant_id}: {document_id}")
                return True
        
        return False
    
    def search_documents(self, tenant_id: str, query: str) -> List[Dict]:
        """Search documents for a tenant with enhanced relevance"""
        if tenant_id not in self.tenant_documents:
            return []
        
        relevant_chunks = []
        query_words = query.lower().split()
        
        for doc in self.tenant_documents[tenant_id]:
            for chunk in doc["chunks"]:
                chunk_lower = chunk.lower()
                # Calculate relevance score
                relevance_score = sum(1 for word in query_words if word in chunk_lower)
                
                if relevance_score > 0:
                    relevant_chunks.append({
                        "content": chunk,
                        "source": doc["filename"],
                        "document_id": doc["document_id"],
                        "relevance_score": relevance_score
                    })
        
        # Sort by relevance and return top matches
        relevant_chunks.sort(key=lambda x: x["relevance_score"], reverse=True)
        return relevant_chunks[:5]  # Return top 5 matches
    
    def get_tenant_stats(self, tenant_id: str) -> Dict:
        """Get comprehensive statistics for a tenant"""
        if tenant_id not in self.tenant_stats:
            return {}
        
        stats = self.tenant_stats[tenant_id].copy()
        stats["tenant_info"] = {
            "company_name": self.tenants.get(tenant_id, {}).get("company_name"),
            "plan": self.tenants.get(tenant_id, {}).get("plan"),
            "status": self.tenants.get(tenant_id, {}).get("status")
        }
        
        return stats
    
    def record_query(self, tenant_id: str, query: str) -> bool:
        """Record a query for analytics"""
        if tenant_id not in self.tenant_stats:
            return False
        
        # Update query stats
        self.tenant_stats[tenant_id]["total_queries"] += 1
        self.tenant_stats[tenant_id]["queries_today"] += 1
        self.tenant_stats[tenant_id]["last_query_date"] = datetime.now().isoformat()
        
        # Track popular queries
        if query not in self.tenant_stats[tenant_id]["popular_queries"]:
            self.tenant_stats[tenant_id]["popular_queries"].append(query)
        
        # Keep only top 10 popular queries
        if len(self.tenant_stats[tenant_id]["popular_queries"]) > 10:
            self.tenant_stats[tenant_id]["popular_queries"] = self.tenant_stats[tenant_id]["popular_queries"][-10:]
        
        self.save_tenant_stats()
        return True

# Global instance
multi_tenant_rag = MultiTenantRAG()


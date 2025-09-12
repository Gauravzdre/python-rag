"""
SQLite Database Module for Multi-Tenant RAG System
Provides persistent storage for tenants, documents, and statistics
"""

import sqlite3
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "rag_database.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    
    def init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create tenants table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tenants (
                    tenant_id TEXT PRIMARY KEY,
                    company_name TEXT NOT NULL,
                    company_domain TEXT UNIQUE NOT NULL,
                    company_email TEXT NOT NULL,
                    company_phone TEXT,
                    api_key TEXT UNIQUE NOT NULL,
                    jwt_secret TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    plan TEXT DEFAULT 'basic',
                    max_documents INTEGER DEFAULT 100,
                    max_queries_per_day INTEGER DEFAULT 1000,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    settings TEXT  -- JSON string for settings
                )
            """)
            
            # Create tenant_documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tenant_documents (
                    document_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    content TEXT NOT NULL,
                    file_type TEXT DEFAULT 'text',
                    upload_time TEXT NOT NULL,
                    chunks TEXT,  -- JSON string for chunks array
                    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id) ON DELETE CASCADE
                )
            """)
            
            # Create tenant_stats table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tenant_stats (
                    tenant_id TEXT PRIMARY KEY,
                    total_documents INTEGER DEFAULT 0,
                    total_queries INTEGER DEFAULT 0,
                    queries_today INTEGER DEFAULT 0,
                    last_query_date TEXT,
                    popular_queries TEXT,  -- JSON string for queries array
                    document_types TEXT,   -- JSON string for types dict
                    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tenant_domain ON tenants (company_domain)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tenant_api_key ON tenants (api_key)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_tenant ON tenant_documents (tenant_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_upload_time ON tenant_documents (upload_time)")
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    def add_tenant(self, tenant_id: str, tenant_data: Dict) -> bool:
        """Add a new tenant"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Convert settings dict to JSON string
                settings_json = json.dumps(tenant_data.get("settings", {}))
                
                cursor.execute("""
                    INSERT INTO tenants (
                        tenant_id, company_name, company_domain, company_email,
                        company_phone, api_key, jwt_secret, status, plan,
                        max_documents, max_queries_per_day, created_at, updated_at, settings
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    tenant_id,
                    tenant_data.get("company_name"),
                    tenant_data.get("company_domain"),
                    tenant_data.get("company_email"),
                    tenant_data.get("company_phone"),
                    tenant_data.get("api_key"),
                    tenant_data.get("jwt_secret"),
                    tenant_data.get("status", "active"),
                    tenant_data.get("plan", "basic"),
                    tenant_data.get("max_documents", 100),
                    tenant_data.get("max_queries_per_day", 1000),
                    tenant_data.get("created_at"),
                    tenant_data.get("updated_at"),
                    settings_json
                ))
                
                # Initialize tenant stats
                cursor.execute("""
                    INSERT INTO tenant_stats (
                        tenant_id, total_documents, total_queries, queries_today,
                        last_query_date, popular_queries, document_types
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    tenant_id,
                    0, 0, 0,
                    None,
                    json.dumps([]),
                    json.dumps({})
                ))
                
                conn.commit()
                logger.info(f"Tenant added to database: {tenant_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error adding tenant {tenant_id}: {e}")
            return False
    
    def get_tenant(self, tenant_id: str) -> Optional[Dict]:
        """Get tenant by ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tenants WHERE tenant_id = ?", (tenant_id,))
                row = cursor.fetchone()
                
                if row:
                    tenant_data = dict(row)
                    # Parse settings JSON
                    tenant_data["settings"] = json.loads(tenant_data["settings"] or "{}")
                    return tenant_data
                return None
                
        except Exception as e:
            logger.error(f"Error getting tenant {tenant_id}: {e}")
            return None
    
    def get_tenant_by_domain(self, domain: str) -> Optional[Dict]:
        """Get tenant by domain"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tenants WHERE company_domain = ?", (domain,))
                row = cursor.fetchone()
                
                if row:
                    tenant_data = dict(row)
                    tenant_data["settings"] = json.loads(tenant_data["settings"] or "{}")
                    return tenant_data
                return None
                
        except Exception as e:
            logger.error(f"Error getting tenant by domain {domain}: {e}")
            return None
    
    def get_tenant_by_api_key(self, api_key: str) -> Optional[Dict]:
        """Get tenant by API key"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tenants WHERE api_key = ?", (api_key,))
                row = cursor.fetchone()
                
                if row:
                    tenant_data = dict(row)
                    tenant_data["settings"] = json.loads(tenant_data["settings"] or "{}")
                    return tenant_data
                return None
                
        except Exception as e:
            logger.error(f"Error getting tenant by API key: {e}")
            return None
    
    def list_tenants(self) -> List[Dict]:
        """List all tenants with basic info"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT t.*, 
                           COUNT(d.document_id) as document_count,
                           COALESCE(s.total_queries, 0) as total_queries
                    FROM tenants t
                    LEFT JOIN tenant_documents d ON t.tenant_id = d.tenant_id
                    LEFT JOIN tenant_stats s ON t.tenant_id = s.tenant_id
                    GROUP BY t.tenant_id
                    ORDER BY t.created_at DESC
                """)
                
                tenants = []
                for row in cursor.fetchall():
                    tenant_data = dict(row)
                    tenant_data["settings"] = json.loads(tenant_data["settings"] or "{}")
                    tenants.append(tenant_data)
                
                return tenants
                
        except Exception as e:
            logger.error(f"Error listing tenants: {e}")
            return []
    
    def update_tenant(self, tenant_id: str, updates: Dict) -> bool:
        """Update tenant"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Handle settings update
                if "settings" in updates:
                    updates["settings"] = json.dumps(updates["settings"])
                
                # Add updated_at timestamp
                updates["updated_at"] = datetime.now().isoformat()
                
                # Build dynamic update query
                set_clauses = []
                values = []
                for key, value in updates.items():
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
                
                if set_clauses:
                    query = f"UPDATE tenants SET {', '.join(set_clauses)} WHERE tenant_id = ?"
                    values.append(tenant_id)
                    cursor.execute(query, values)
                    conn.commit()
                    
                    logger.info(f"Tenant updated: {tenant_id}")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error updating tenant {tenant_id}: {e}")
            return False
    
    def delete_tenant(self, tenant_id: str) -> bool:
        """Delete tenant and all associated data"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Delete tenant (cascade will handle related records)
                cursor.execute("DELETE FROM tenants WHERE tenant_id = ?", (tenant_id,))
                conn.commit()
                
                logger.info(f"Tenant deleted: {tenant_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting tenant {tenant_id}: {e}")
            return False
    
    def add_document(self, tenant_id: str, document_data: Dict) -> bool:
        """Add document to tenant"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Convert chunks to JSON string
                chunks_json = json.dumps(document_data.get("chunks", []))
                
                cursor.execute("""
                    INSERT INTO tenant_documents (
                        document_id, tenant_id, filename, content, file_type, upload_time, chunks
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    document_data.get("document_id"),
                    tenant_id,
                    document_data.get("filename"),
                    document_data.get("content"),
                    document_data.get("file_type", "text"),
                    document_data.get("upload_time"),
                    chunks_json
                ))
                
                # Update tenant stats
                file_type = document_data.get("file_type", "text")
                cursor.execute("""
                    UPDATE tenant_stats 
                    SET total_documents = total_documents + 1
                    WHERE tenant_id = ?
                """, (tenant_id,))
                
                # Update document types
                cursor.execute("SELECT document_types FROM tenant_stats WHERE tenant_id = ?", (tenant_id,))
                row = cursor.fetchone()
                if row:
                    doc_types = json.loads(row[0] or "{}")
                    doc_types[file_type] = doc_types.get(file_type, 0) + 1
                    cursor.execute("""
                        UPDATE tenant_stats 
                        SET document_types = ?
                        WHERE tenant_id = ?
                    """, (json.dumps(doc_types), tenant_id))
                
                conn.commit()
                logger.info(f"Document added to tenant {tenant_id}: {document_data.get('filename')}")
                return True
                
        except Exception as e:
            logger.error(f"Error adding document to tenant {tenant_id}: {e}")
            return False
    
    def get_tenant_documents(self, tenant_id: str) -> List[Dict]:
        """Get all documents for a tenant"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM tenant_documents 
                    WHERE tenant_id = ? 
                    ORDER BY upload_time DESC
                """, (tenant_id,))
                
                documents = []
                for row in cursor.fetchall():
                    doc_data = dict(row)
                    doc_data["chunks"] = json.loads(doc_data["chunks"] or "[]")
                    documents.append(doc_data)
                
                return documents
                
        except Exception as e:
            logger.error(f"Error getting documents for tenant {tenant_id}: {e}")
            return []
    
    def delete_document(self, tenant_id: str, document_id: str) -> bool:
        """Delete a specific document"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get document info before deletion
                cursor.execute("""
                    SELECT file_type FROM tenant_documents 
                    WHERE tenant_id = ? AND document_id = ?
                """, (tenant_id, document_id))
                row = cursor.fetchone()
                
                if not row:
                    return False
                
                file_type = row[0]
                
                # Delete document
                cursor.execute("""
                    DELETE FROM tenant_documents 
                    WHERE tenant_id = ? AND document_id = ?
                """, (tenant_id, document_id))
                
                # Update stats
                cursor.execute("""
                    UPDATE tenant_stats 
                    SET total_documents = total_documents - 1
                    WHERE tenant_id = ?
                """, (tenant_id,))
                
                # Update document types
                cursor.execute("SELECT document_types FROM tenant_stats WHERE tenant_id = ?", (tenant_id,))
                row = cursor.fetchone()
                if row:
                    doc_types = json.loads(row[0] or "{}")
                    if file_type in doc_types:
                        doc_types[file_type] = max(0, doc_types[file_type] - 1)
                        if doc_types[file_type] == 0:
                            del doc_types[file_type]
                        cursor.execute("""
                            UPDATE tenant_stats 
                            SET document_types = ?
                            WHERE tenant_id = ?
                        """, (json.dumps(doc_types), tenant_id))
                
                conn.commit()
                logger.info(f"Document deleted from tenant {tenant_id}: {document_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting document {document_id} from tenant {tenant_id}: {e}")
            return False
    
    def get_tenant_stats(self, tenant_id: str) -> Optional[Dict]:
        """Get tenant statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT s.*, t.company_name, t.plan, t.status
                    FROM tenant_stats s
                    JOIN tenants t ON s.tenant_id = t.tenant_id
                    WHERE s.tenant_id = ?
                """, (tenant_id,))
                
                row = cursor.fetchone()
                if row:
                    stats = dict(row)
                    stats["popular_queries"] = json.loads(stats["popular_queries"] or "[]")
                    stats["document_types"] = json.loads(stats["document_types"] or "{}")
                    stats["tenant_info"] = {
                        "company_name": stats["company_name"],
                        "plan": stats["plan"],
                        "status": stats["status"]
                    }
                    return stats
                return None
                
        except Exception as e:
            logger.error(f"Error getting stats for tenant {tenant_id}: {e}")
            return None
    
    def record_query(self, tenant_id: str, query: str) -> bool:
        """Record a query for analytics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Update query stats
                cursor.execute("""
                    UPDATE tenant_stats 
                    SET total_queries = total_queries + 1,
                        queries_today = queries_today + 1,
                        last_query_date = ?
                    WHERE tenant_id = ?
                """, (datetime.now().isoformat(), tenant_id))
                
                # Update popular queries
                cursor.execute("SELECT popular_queries FROM tenant_stats WHERE tenant_id = ?", (tenant_id,))
                row = cursor.fetchone()
                if row:
                    popular_queries = json.loads(row[0] or "[]")
                    if query not in popular_queries:
                        popular_queries.append(query)
                    
                    # Keep only top 10
                    if len(popular_queries) > 10:
                        popular_queries = popular_queries[-10:]
                    
                    cursor.execute("""
                        UPDATE tenant_stats 
                        SET popular_queries = ?
                        WHERE tenant_id = ?
                    """, (json.dumps(popular_queries), tenant_id))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error recording query for tenant {tenant_id}: {e}")
            return False
    
    def search_documents(self, tenant_id: str, query: str) -> List[Dict]:
        """Search documents for a tenant"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT document_id, filename, content, chunks
                    FROM tenant_documents 
                    WHERE tenant_id = ?
                """, (tenant_id,))
                
                relevant_chunks = []
                query_words = query.lower().split()
                
                for row in cursor.fetchall():
                    doc_data = dict(row)
                    chunks = json.loads(doc_data["chunks"] or "[]")
                    
                    for chunk in chunks:
                        chunk_lower = chunk.lower()
                        relevance_score = sum(1 for word in query_words if word in chunk_lower)
                        
                        if relevance_score > 0:
                            relevant_chunks.append({
                                "content": chunk,
                                "source": doc_data["filename"],
                                "document_id": doc_data["document_id"],
                                "relevance_score": relevance_score
                            })
                
                # Sort by relevance and return top matches
                relevant_chunks.sort(key=lambda x: x["relevance_score"], reverse=True)
                return relevant_chunks[:5]
                
        except Exception as e:
            logger.error(f"Error searching documents for tenant {tenant_id}: {e}")
            return []
    
    def migrate_from_json(self, json_files: Dict[str, str]) -> bool:
        """Migrate data from JSON files to database"""
        try:
            logger.info("Starting migration from JSON files to database...")
            
            # Migrate tenants
            if os.path.exists(json_files.get("tenants", "tenants.json")):
                with open(json_files["tenants"], "r") as f:
                    tenants_data = json.load(f)
                
                for tenant_id, tenant_data in tenants_data.items():
                    if not self.get_tenant(tenant_id):
                        self.add_tenant(tenant_id, tenant_data)
                        logger.info(f"Migrated tenant: {tenant_id}")
            
            # Migrate documents
            if os.path.exists(json_files.get("documents", "tenant_documents.json")):
                with open(json_files["documents"], "r") as f:
                    documents_data = json.load(f)
                
                for tenant_id, docs in documents_data.items():
                    for doc in docs:
                        self.add_document(tenant_id, doc)
                        logger.info(f"Migrated document: {doc.get('filename')} for tenant {tenant_id}")
            
            # Migrate stats
            if os.path.exists(json_files.get("stats", "tenant_stats.json")):
                with open(json_files["stats"], "r") as f:
                    stats_data = json.load(f)
                
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    for tenant_id, stats in stats_data.items():
                        cursor.execute("""
                            UPDATE tenant_stats 
                            SET total_documents = ?, total_queries = ?, queries_today = ?,
                                last_query_date = ?, popular_queries = ?, document_types = ?
                            WHERE tenant_id = ?
                        """, (
                            stats.get("total_documents", 0),
                            stats.get("total_queries", 0),
                            stats.get("queries_today", 0),
                            stats.get("last_query_date"),
                            json.dumps(stats.get("popular_queries", [])),
                            json.dumps(stats.get("document_types", {})),
                            tenant_id
                        ))
                    conn.commit()
            
            logger.info("Migration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during migration: {e}")
            return False

# Global database instance
db_manager = DatabaseManager()

"""
PostgreSQL Database Module for Multi-Tenant RAG System
Provides persistent storage using Neon PostgreSQL
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Integer, DateTime, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

class PostgreSQLManager:
    def __init__(self):
        # Get database URL from environment variable
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            # Fallback to Neon connection string format
            self.database_url = "postgresql://neondb_owner:npg_b8wgFRi6fOTZ@ep-lively-haze-adxb4l5a-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
        
        # Create engine and session
        self.engine = create_engine(self.database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.metadata = MetaData()
        
        # Initialize tables
        self.init_database()
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def init_database(self):
        """Initialize database tables"""
        try:
            # Define tables
            tenants_table = Table(
                'tenants', self.metadata,
                Column('tenant_id', String(255), primary_key=True),
                Column('company_name', String(255), nullable=False),
                Column('company_domain', String(255), unique=True, nullable=False),
                Column('company_email', String(255), nullable=False),
                Column('company_phone', String(50)),
                Column('api_key', String(255), unique=True, nullable=False),
                Column('jwt_secret', String(255), nullable=False),
                Column('status', String(50), default='active'),
                Column('plan', String(50), default='basic'),
                Column('max_documents', Integer, default=100),
                Column('max_queries_per_day', Integer, default=1000),
                Column('created_at', DateTime, nullable=False),
                Column('updated_at', DateTime, nullable=False),
                Column('settings', Text)  # JSON string
            )
            
            tenant_documents_table = Table(
                'tenant_documents', self.metadata,
                Column('document_id', String(255), primary_key=True),
                Column('tenant_id', String(255), nullable=False),
                Column('filename', String(255), nullable=False),
                Column('content', Text, nullable=False),
                Column('file_type', String(50), default='text'),
                Column('upload_time', DateTime, nullable=False),
                Column('chunks', Text)  # JSON string
            )
            
            tenant_stats_table = Table(
                'tenant_stats', self.metadata,
                Column('tenant_id', String(255), primary_key=True),
                Column('total_documents', Integer, default=0),
                Column('total_queries', Integer, default=0),
                Column('queries_today', Integer, default=0),
                Column('last_query_date', DateTime),
                Column('popular_queries', Text),  # JSON string
                Column('document_types', Text)    # JSON string
            )
            
            # Create tables
            self.metadata.create_all(self.engine)
            logger.info("PostgreSQL database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing PostgreSQL database: {e}")
            raise
    
    def add_tenant(self, tenant_id: str, tenant_data: Dict) -> bool:
        """Add a new tenant"""
        try:
            with self.get_session() as session:
                # Convert settings dict to JSON string
                settings_json = json.dumps(tenant_data.get("settings", {}))
                
                # Insert tenant
                session.execute(text("""
                    INSERT INTO tenants (
                        tenant_id, company_name, company_domain, company_email,
                        company_phone, api_key, jwt_secret, status, plan,
                        max_documents, max_queries_per_day, created_at, updated_at, settings
                    ) VALUES (
                        :tenant_id, :company_name, :company_domain, :company_email,
                        :company_phone, :api_key, :jwt_secret, :status, :plan,
                        :max_documents, :max_queries_per_day, :created_at, :updated_at, :settings
                    )
                """), {
                    'tenant_id': tenant_id,
                    'company_name': tenant_data.get("company_name"),
                    'company_domain': tenant_data.get("company_domain"),
                    'company_email': tenant_data.get("company_email"),
                    'company_phone': tenant_data.get("company_phone"),
                    'api_key': tenant_data.get("api_key"),
                    'jwt_secret': tenant_data.get("jwt_secret"),
                    'status': tenant_data.get("status", "active"),
                    'plan': tenant_data.get("plan", "basic"),
                    'max_documents': tenant_data.get("max_documents", 100),
                    'max_queries_per_day': tenant_data.get("max_queries_per_day", 1000),
                    'created_at': tenant_data.get("created_at"),
                    'updated_at': tenant_data.get("updated_at"),
                    'settings': settings_json
                })
                
                # Initialize tenant stats
                session.execute(text("""
                    INSERT INTO tenant_stats (
                        tenant_id, total_documents, total_queries, queries_today,
                        last_query_date, popular_queries, document_types
                    ) VALUES (
                        :tenant_id, :total_documents, :total_queries, :queries_today,
                        :last_query_date, :popular_queries, :document_types
                    )
                """), {
                    'tenant_id': tenant_id,
                    'total_documents': 0,
                    'total_queries': 0,
                    'queries_today': 0,
                    'last_query_date': None,
                    'popular_queries': json.dumps([]),
                    'document_types': json.dumps({})
                })
                
                session.commit()
                logger.info(f"Tenant added to PostgreSQL: {tenant_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error adding tenant {tenant_id}: {e}")
            return False
    
    def get_tenant(self, tenant_id: str) -> Optional[Dict]:
        """Get tenant by ID"""
        try:
            with self.get_session() as session:
                result = session.execute(text("""
                    SELECT * FROM tenants WHERE tenant_id = :tenant_id
                """), {'tenant_id': tenant_id})
                
                row = result.fetchone()
                if row:
                    tenant_data = dict(row._mapping)
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
            with self.get_session() as session:
                result = session.execute(text("""
                    SELECT * FROM tenants WHERE company_domain = :domain
                """), {'domain': domain})
                
                row = result.fetchone()
                if row:
                    tenant_data = dict(row._mapping)
                    tenant_data["settings"] = json.loads(tenant_data["settings"] or "{}")
                    return tenant_data
                return None
                
        except Exception as e:
            logger.error(f"Error getting tenant by domain {domain}: {e}")
            return None
    
    def get_tenant_by_api_key(self, api_key: str) -> Optional[Dict]:
        """Get tenant by API key"""
        try:
            with self.get_session() as session:
                result = session.execute(text("""
                    SELECT * FROM tenants WHERE api_key = :api_key
                """), {'api_key': api_key})
                
                row = result.fetchone()
                if row:
                    tenant_data = dict(row._mapping)
                    tenant_data["settings"] = json.loads(tenant_data["settings"] or "{}")
                    return tenant_data
                return None
                
        except Exception as e:
            logger.error(f"Error getting tenant by API key: {e}")
            return None
    
    def list_tenants(self) -> List[Dict]:
        """List all tenants with basic info"""
        try:
            with self.get_session() as session:
                result = session.execute(text("""
                    SELECT t.*, 
                           COUNT(d.document_id) as document_count,
                           COALESCE(s.total_queries, 0) as total_queries
                    FROM tenants t
                    LEFT JOIN tenant_documents d ON t.tenant_id = d.tenant_id
                    LEFT JOIN tenant_stats s ON t.tenant_id = s.tenant_id
                    GROUP BY t.tenant_id, t.company_name, t.company_domain, t.company_email,
                             t.company_phone, t.api_key, t.jwt_secret, t.status, t.plan,
                             t.max_documents, t.max_queries_per_day, t.created_at, t.updated_at, t.settings
                    ORDER BY t.created_at DESC
                """))
                
                tenants = []
                for row in result:
                    tenant_data = dict(row._mapping)
                    tenant_data["settings"] = json.loads(tenant_data["settings"] or "{}")
                    tenants.append(tenant_data)
                
                return tenants
                
        except Exception as e:
            logger.error(f"Error listing tenants: {e}")
            return []
    
    def update_tenant(self, tenant_id: str, updates: Dict) -> bool:
        """Update tenant"""
        try:
            with self.get_session() as session:
                # Handle settings update
                if "settings" in updates:
                    updates["settings"] = json.dumps(updates["settings"])
                
                # Add updated_at timestamp
                updates["updated_at"] = datetime.now().isoformat()
                
                # Build dynamic update query
                set_clauses = []
                values = {'tenant_id': tenant_id}
                
                for key, value in updates.items():
                    set_clauses.append(f"{key} = :{key}")
                    values[key] = value
                
                if set_clauses:
                    query = f"UPDATE tenants SET {', '.join(set_clauses)} WHERE tenant_id = :tenant_id"
                    session.execute(text(query), values)
                    session.commit()
                    
                    logger.info(f"Tenant updated: {tenant_id}")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error updating tenant {tenant_id}: {e}")
            return False
    
    def delete_tenant(self, tenant_id: str) -> bool:
        """Delete tenant and all associated data"""
        try:
            with self.get_session() as session:
                # Delete tenant (cascade will handle related records)
                session.execute(text("DELETE FROM tenants WHERE tenant_id = :tenant_id"), 
                              {'tenant_id': tenant_id})
                session.commit()
                
                logger.info(f"Tenant deleted: {tenant_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting tenant {tenant_id}: {e}")
            return False
    
    def add_document(self, tenant_id: str, document_data: Dict) -> bool:
        """Add document to tenant"""
        try:
            with self.get_session() as session:
                # Convert chunks to JSON string
                chunks_json = json.dumps(document_data.get("chunks", []))
                
                session.execute(text("""
                    INSERT INTO tenant_documents (
                        document_id, tenant_id, filename, content, file_type, upload_time, chunks
                    ) VALUES (
                        :document_id, :tenant_id, :filename, :content, :file_type, :upload_time, :chunks
                    )
                """), {
                    'document_id': document_data.get("document_id"),
                    'tenant_id': tenant_id,
                    'filename': document_data.get("filename"),
                    'content': document_data.get("content"),
                    'file_type': document_data.get("file_type", "text"),
                    'upload_time': document_data.get("upload_time"),
                    'chunks': chunks_json
                })
                
                # Update tenant stats
                file_type = document_data.get("file_type", "text")
                session.execute(text("""
                    UPDATE tenant_stats 
                    SET total_documents = total_documents + 1
                    WHERE tenant_id = :tenant_id
                """), {'tenant_id': tenant_id})
                
                # Update document types
                result = session.execute(text("""
                    SELECT document_types FROM tenant_stats WHERE tenant_id = :tenant_id
                """), {'tenant_id': tenant_id})
                
                row = result.fetchone()
                if row:
                    doc_types = json.loads(row[0] or "{}")
                    doc_types[file_type] = doc_types.get(file_type, 0) + 1
                    session.execute(text("""
                        UPDATE tenant_stats 
                        SET document_types = :document_types
                        WHERE tenant_id = :tenant_id
                    """), {'document_types': json.dumps(doc_types), 'tenant_id': tenant_id})
                
                session.commit()
                logger.info(f"Document added to tenant {tenant_id}: {document_data.get('filename')}")
                return True
                
        except Exception as e:
            logger.error(f"Error adding document to tenant {tenant_id}: {e}")
            return False
    
    def get_tenant_documents(self, tenant_id: str) -> List[Dict]:
        """Get all documents for a tenant"""
        try:
            with self.get_session() as session:
                result = session.execute(text("""
                    SELECT * FROM tenant_documents 
                    WHERE tenant_id = :tenant_id 
                    ORDER BY upload_time DESC
                """), {'tenant_id': tenant_id})
                
                documents = []
                for row in result:
                    doc_data = dict(row._mapping)
                    doc_data["chunks"] = json.loads(doc_data["chunks"] or "[]")
                    documents.append(doc_data)
                
                return documents
                
        except Exception as e:
            logger.error(f"Error getting documents for tenant {tenant_id}: {e}")
            return []
    
    def delete_document(self, tenant_id: str, document_id: str) -> bool:
        """Delete a specific document"""
        try:
            with self.get_session() as session:
                # Get document info before deletion
                result = session.execute(text("""
                    SELECT file_type FROM tenant_documents 
                    WHERE tenant_id = :tenant_id AND document_id = :document_id
                """), {'tenant_id': tenant_id, 'document_id': document_id})
                
                row = result.fetchone()
                if not row:
                    return False
                
                file_type = row[0]
                
                # Delete document
                session.execute(text("""
                    DELETE FROM tenant_documents 
                    WHERE tenant_id = :tenant_id AND document_id = :document_id
                """), {'tenant_id': tenant_id, 'document_id': document_id})
                
                # Update stats
                session.execute(text("""
                    UPDATE tenant_stats 
                    SET total_documents = total_documents - 1
                    WHERE tenant_id = :tenant_id
                """), {'tenant_id': tenant_id})
                
                # Update document types
                result = session.execute(text("""
                    SELECT document_types FROM tenant_stats WHERE tenant_id = :tenant_id
                """), {'tenant_id': tenant_id})
                
                row = result.fetchone()
                if row:
                    doc_types = json.loads(row[0] or "{}")
                    if file_type in doc_types:
                        doc_types[file_type] = max(0, doc_types[file_type] - 1)
                        if doc_types[file_type] == 0:
                            del doc_types[file_type]
                        session.execute(text("""
                            UPDATE tenant_stats 
                            SET document_types = :document_types
                            WHERE tenant_id = :tenant_id
                        """), {'document_types': json.dumps(doc_types), 'tenant_id': tenant_id})
                
                session.commit()
                logger.info(f"Document deleted from tenant {tenant_id}: {document_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting document {document_id} from tenant {tenant_id}: {e}")
            return False
    
    def get_tenant_stats(self, tenant_id: str) -> Optional[Dict]:
        """Get tenant statistics"""
        try:
            with self.get_session() as session:
                result = session.execute(text("""
                    SELECT s.*, t.company_name, t.plan, t.status
                    FROM tenant_stats s
                    JOIN tenants t ON s.tenant_id = t.tenant_id
                    WHERE s.tenant_id = :tenant_id
                """), {'tenant_id': tenant_id})
                
                row = result.fetchone()
                if row:
                    stats = dict(row._mapping)
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
            with self.get_session() as session:
                # Update query stats
                session.execute(text("""
                    UPDATE tenant_stats 
                    SET total_queries = total_queries + 1,
                        queries_today = queries_today + 1,
                        last_query_date = :last_query_date
                    WHERE tenant_id = :tenant_id
                """), {
                    'tenant_id': tenant_id,
                    'last_query_date': datetime.now().isoformat()
                })
                
                # Update popular queries
                result = session.execute(text("""
                    SELECT popular_queries FROM tenant_stats WHERE tenant_id = :tenant_id
                """), {'tenant_id': tenant_id})
                
                row = result.fetchone()
                if row:
                    popular_queries = json.loads(row[0] or "[]")
                    if query not in popular_queries:
                        popular_queries.append(query)
                    
                    # Keep only top 10
                    if len(popular_queries) > 10:
                        popular_queries = popular_queries[-10:]
                    
                    session.execute(text("""
                        UPDATE tenant_stats 
                        SET popular_queries = :popular_queries
                        WHERE tenant_id = :tenant_id
                    """), {
                        'popular_queries': json.dumps(popular_queries),
                        'tenant_id': tenant_id
                    })
                
                session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error recording query for tenant {tenant_id}: {e}")
            return False
    
    def search_documents(self, tenant_id: str, query: str) -> List[Dict]:
        """Search documents for a tenant"""
        try:
            with self.get_session() as session:
                result = session.execute(text("""
                    SELECT document_id, filename, content, chunks
                    FROM tenant_documents 
                    WHERE tenant_id = :tenant_id
                """), {'tenant_id': tenant_id})
                
                relevant_chunks = []
                query_words = query.lower().split()
                
                for row in result:
                    doc_data = dict(row._mapping)
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
        """Migrate data from JSON files to PostgreSQL"""
        try:
            logger.info("Starting migration from JSON files to PostgreSQL...")
            
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
                
                with self.get_session() as session:
                    for tenant_id, stats in stats_data.items():
                        session.execute(text("""
                            UPDATE tenant_stats 
                            SET total_documents = :total_documents, 
                                total_queries = :total_queries, 
                                queries_today = :queries_today,
                                last_query_date = :last_query_date, 
                                popular_queries = :popular_queries, 
                                document_types = :document_types
                            WHERE tenant_id = :tenant_id
                        """), {
                            'tenant_id': tenant_id,
                            'total_documents': stats.get("total_documents", 0),
                            'total_queries': stats.get("total_queries", 0),
                            'queries_today': stats.get("queries_today", 0),
                            'last_query_date': stats.get("last_query_date"),
                            'popular_queries': json.dumps(stats.get("popular_queries", [])),
                            'document_types': json.dumps(stats.get("document_types", {}))
                        })
                    session.commit()
            
            logger.info("Migration to PostgreSQL completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during migration to PostgreSQL: {e}")
            return False

# Global PostgreSQL instance
postgres_manager = PostgreSQLManager()

"""
Multi-Tenant RAG Engine
Handles document processing and querying for specific tenants
"""

import os
import io
import tempfile
from typing import List, Dict, Optional
from pathlib import Path
import logging

# Core dependencies
from dotenv import load_dotenv
import httpx

# LangChain imports (simplified for cost-effectiveness)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# Document processing
import PyPDF2
from pypdf import PdfReader
import json
from datetime import datetime

# Multi-tenant system
from app.multi_tenant import multi_tenant_rag

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class MultiTenantRAGEngine:
    def __init__(self):
        """Initialize the multi-tenant RAG engine"""
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        logger.info("Multi-Tenant RAG Engine initialized")
    
    def process_document_upload(self, tenant_id: str, file) -> Dict:
        """
        Process uploaded document for a specific tenant
        
        Args:
            tenant_id: The tenant (company) ID
            file: FastAPI UploadFile object
            
        Returns:
            Dict with processing results
        """
        try:
            # Verify tenant exists
            if not multi_tenant_rag.get_tenant(tenant_id):
                return {"chunks": 0, "status": "error", "message": f"Tenant {tenant_id} not found"}
            
            # Read file content based on file type
            content = self._extract_content(file)
            logger.info(f"Extracted content length: {len(content) if content else 0} characters")
            
            if not content:
                return {"chunks": 0, "status": "error", "message": "Could not extract content from file"}
            
            # Get file type
            file_type = self._get_file_type(file.filename)
            
            # Add document to tenant
            success = multi_tenant_rag.add_document(
                tenant_id=tenant_id,
                filename=file.filename,
                content=content,
                file_type=file_type
            )
            
            if not success:
                return {"chunks": 0, "status": "error", "message": "Failed to add document to tenant"}
            
            # Get the newly uploaded document to count its chunks
            documents = multi_tenant_rag.get_tenant_documents(tenant_id)
            # Find the most recent document (should be the one we just uploaded)
            if documents:
                latest_doc = max(documents, key=lambda x: x.get("upload_time", ""))
                chunk_count = len(latest_doc.get("chunks", []))
            else:
                chunk_count = 0
            
            logger.info(f"Document processed for tenant {tenant_id}: {file.filename} - {chunk_count} chunks")
            
            return {
                "chunks": chunk_count,
                "status": "success",
                "message": f"Document processed successfully for tenant {tenant_id}",
                "tenant_id": tenant_id,
                "filename": file.filename,
                "file_type": file_type
            }
            
        except Exception as e:
            logger.error(f"Error processing document for tenant {tenant_id}: {e}")
            return {"chunks": 0, "status": "error", "message": str(e)}
    
    def _extract_content(self, file) -> str:
        """Extract content from uploaded file based on file type"""
        filename = file.filename.lower()
        
        try:
            if filename.endswith('.pdf'):
                return self._extract_pdf_content(file)
            elif filename.endswith(('.txt', '.md')):
                return self._extract_text_content(file)
            elif filename.endswith('.json'):
                return self._extract_json_content(file)
            else:
                # Try to read as text
                return self._extract_text_content(file)
                
        except Exception as e:
            logger.error(f"Error extracting content from {file.filename}: {e}")
            return ""
    
    def _extract_pdf_content(self, file) -> str:
        """Extract text content from PDF file"""
        try:
            # Read PDF content
            pdf_content = file.file.read()
            
            # Create PDF reader
            pdf_reader = PdfReader(io.BytesIO(pdf_content))
            
            # Extract text from all pages
            text_content = ""
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_content += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
            
            logger.info(f"Extracted {len(text_content)} characters from PDF: {file.filename}")
            return text_content
            
        except Exception as e:
            logger.error(f"Error extracting PDF content: {e}")
            # Fallback to PyPDF2
            try:
                file.file.seek(0)  # Reset file pointer
                pdf_content = file.file.read()
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
                
                text_content = ""
                for page in pdf_reader.pages:
                    text_content += page.extract_text() + "\n"
                
                return text_content
            except Exception as e2:
                logger.error(f"PyPDF2 fallback also failed: {e2}")
                return ""
    
    def _extract_text_content(self, file) -> str:
        """Extract text content from text file"""
        try:
            content = file.file.read().decode('utf-8')
            return content
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                file.file.seek(0)
                content = file.file.read().decode('latin-1')
                return content
            except Exception as e:
                logger.error(f"Error decoding text file: {e}")
                return ""
    
    def _extract_json_content(self, file) -> str:
        """Extract and format JSON content"""
        try:
            content = file.file.read().decode('utf-8')
            json_data = json.loads(content)
            # Convert JSON to readable text
            return json.dumps(json_data, indent=2)
        except Exception as e:
            logger.error(f"Error processing JSON file: {e}")
            return ""
    
    def _get_file_type(self, filename: str) -> str:
        """Get file type from filename"""
        if filename.lower().endswith('.pdf'):
            return 'pdf'
        elif filename.lower().endswith(('.txt', '.md')):
            return 'text'
        elif filename.lower().endswith('.json'):
            return 'json'
        else:
            return 'unknown'
    
    async def process_query(self, tenant_id: str, query: str) -> Dict:
        """
        Process query for a specific tenant
        
        Args:
            tenant_id: The tenant (company) ID
            query: User query string
            
        Returns:
            Dict with answer and sources
        """
        try:
            # Verify tenant exists
            tenant_info = multi_tenant_rag.get_tenant(tenant_id)
            if not tenant_info:
                return {"answer": f"Tenant {tenant_id} not found", "sources": []}
            
            # Check if tenant is active
            if tenant_info.get("status") != "active":
                return {"answer": f"Tenant {tenant_id} is not active", "sources": []}
            
            # Record query for analytics
            multi_tenant_rag.record_query(tenant_id, query)
            
            # Get relevant documents for tenant
            relevant_chunks = multi_tenant_rag.search_documents(tenant_id, query)
            
            if not relevant_chunks:
                return {
                    "answer": f"No relevant information found in {tenant_info.get('company_name', 'your company')}'s documents.",
                    "sources": []
                }
            
            # Prepare context
            context = "\n\n".join([chunk['content'] for chunk in relevant_chunks[:3]])
            sources = [{"source": chunk['source']} for chunk in relevant_chunks[:3]]
            
            # Get tenant-specific AI personality
            ai_personality = tenant_info.get("settings", {}).get("ai_personality", "helpful")
            response_style = tenant_info.get("settings", {}).get("response_style", "concise")
            company_name = tenant_info.get("company_name", "the company")
            
            # Call OpenRouter API with tenant-specific context
            response = httpx.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": f"RAG Chatbot - {company_name}"
                },
                json={
                    "model": "meta-llama/llama-3.2-3b-instruct:free",  # Free model
                    "messages": [
                        {
                            "role": "system", 
                            "content": f"You are a {ai_personality} AI assistant for {company_name}. Keep responses {response_style} (2-3 sentences max). Focus on key points only. Be enthusiastic but brief."
                        },
                        {
                            "role": "user", 
                            "content": f"Context from {company_name}'s documents: {context}\n\nQuestion: {query}\n\nKeep your response SHORT and to the point."
                        }
                    ],
                    "max_tokens": 150,
                    "temperature": 0.7
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result["choices"][0]["message"]["content"]
                return {"answer": answer, "sources": sources, "tenant_id": tenant_id}
            else:
                return {"answer": f"Error from OpenRouter API: {response.status_code}", "sources": sources}
                
        except Exception as e:
            logger.error(f"Error processing query for tenant {tenant_id}: {e}")
            return {"answer": f"Error processing query: {str(e)}", "sources": []}
    
    def get_tenant_document_count(self, tenant_id: str) -> int:
        """Get the number of documents for a specific tenant"""
        documents = multi_tenant_rag.get_tenant_documents(tenant_id)
        return len(documents)
    
    def get_tenant_collection_info(self, tenant_id: str) -> Dict:
        """Get information about a tenant's document collection"""
        tenant_info = multi_tenant_rag.get_tenant(tenant_id)
        if not tenant_info:
            return {"error": f"Tenant {tenant_id} not found"}
        
        documents = multi_tenant_rag.get_tenant_documents(tenant_id)
        stats = multi_tenant_rag.get_tenant_stats(tenant_id)
        
        return {
            "tenant_id": tenant_id,
            "company_name": tenant_info.get("company_name"),
            "document_count": len(documents),
            "storage_type": "tenant_specific",
            "llm_provider": "openrouter",
            "model": "meta-llama/llama-3.2-3b-instruct:free",
            "plan": tenant_info.get("plan"),
            "status": tenant_info.get("status"),
            "total_queries": stats.get("total_queries", 0),
            "queries_today": stats.get("queries_today", 0)
        }

# Global instance
multi_tenant_rag_engine = MultiTenantRAGEngine()

# Backward compatibility functions
def process_document_upload(tenant_id: str, file):
    """Backward compatible function for document upload"""
    result = multi_tenant_rag_engine.process_document_upload(tenant_id, file)
    return result["chunks"]

async def process_query(tenant_id: str, query: str):
    """Backward compatible function for query processing"""
    return await multi_tenant_rag_engine.process_query(tenant_id, query)

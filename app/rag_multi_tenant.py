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
import time

# LangChain imports (simplified for cost-effectiveness)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# Vector embeddings and semantic search
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np

# Document processing
import PyPDF2
from pypdf import PdfReader
import json
from datetime import datetime
from pathlib import Path

# Multi-tenant system
from app.multi_tenant import multi_tenant_rag

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables, handle errors gracefully
try:
    load_dotenv()
except Exception as e:
    logger.warning(f"Could not load .env file: {e}")

class MultiTenantRAGEngine:
    def __init__(self):
        """Initialize the multi-tenant RAG engine with vector embeddings"""
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        
        # Initialize text splitter with optimized settings
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,  # Slightly smaller for better precision
            chunk_overlap=150,  # Better overlap for context continuity
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Initialize vector embeddings (free, local)
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # Fast, lightweight, free
            logger.info("✅ Vector embeddings initialized (sentence-transformers)")
        except Exception as e:
            logger.warning(f"Could not load embedding model: {e}")
            self.embedding_model = None
        
        # Initialize ChromaDB for vector storage
        try:
            chroma_dir = Path("./chroma_db")
            chroma_dir.mkdir(exist_ok=True)
            self.chroma_client = chromadb.PersistentClient(
                path=str(chroma_dir),
                settings=Settings(anonymized_telemetry=False)
            )
            logger.info("✅ ChromaDB vector database initialized")
        except Exception as e:
            logger.warning(f"Could not initialize ChromaDB: {e}")
            self.chroma_client = None
        
        logger.info("Multi-Tenant RAG Engine initialized with advanced features")
    
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
            
            # Add document to tenant (PostgreSQL)
            success = multi_tenant_rag.add_document(
                tenant_id=tenant_id,
                filename=file.filename,
                content=content,
                file_type=file_type
            )
            
            if not success:
                return {"chunks": 0, "status": "error", "message": "Failed to add document to tenant"}
            
            # Store vectors in ChromaDB for semantic search
            if self.embedding_model and self.chroma_client:
                self._store_vectors(tenant_id, file.filename, content)
            
            # Get the newly uploaded document to count its chunks
            documents = multi_tenant_rag.get_tenant_documents(tenant_id)
            logger.info(f"Retrieved {len(documents)} documents for tenant {tenant_id}")
            
            # Find the most recent document (should be the one we just uploaded)
            if documents:
                latest_doc = max(documents, key=lambda x: x.get("upload_time", ""))
                chunks = latest_doc.get("chunks", [])
                chunk_count = len(chunks)
                logger.info(f"Latest document: {latest_doc.get('filename')}, chunks: {chunk_count}")
                logger.info(f"Chunks data type: {type(chunks)}, first chunk: {chunks[0] if chunks else 'None'}")
            else:
                chunk_count = 0
                logger.warning(f"No documents found for tenant {tenant_id}")
            
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
    
    def _advanced_retrieval(self, tenant_id: str, query: str) -> List[Dict]:
        """
        Advanced retrieval using multi-query and hybrid search (keyword + semantic)
        Based on LangChain advanced RAG techniques
        """
        # Step 1: Multi-query generation (generate query variations)
        query_variations = self._generate_query_variations(query)
        
        # Step 2: Hybrid search - combine keyword and semantic search
        all_chunks = []
        seen_chunks = set()
        
        # Keyword-based search (existing method)
        keyword_chunks = multi_tenant_rag.search_documents(tenant_id, query)
        for chunk in keyword_chunks:
            chunk_id = f"{chunk.get('document_id', '')}_{chunk.get('content', '')[:50]}"
            if chunk_id not in seen_chunks:
                chunk['search_type'] = 'keyword'
                chunk['score'] = chunk.get('relevance_score', 0) * 0.5  # Weight keyword results
                all_chunks.append(chunk)
                seen_chunks.add(chunk_id)
        
        # Semantic search using vector embeddings
        if self.embedding_model and self.chroma_client:
            semantic_chunks = self._semantic_search(tenant_id, query, query_variations)
            for chunk in semantic_chunks:
                chunk_id = f"{chunk.get('document_id', '')}_{chunk.get('content', '')[:50]}"
                if chunk_id not in seen_chunks:
                    chunk['search_type'] = 'semantic'
                    all_chunks.append(chunk)
                    seen_chunks.add(chunk_id)
                else:
                    # Boost score if found in both searches
                    for existing in all_chunks:
                        if existing.get('document_id') == chunk.get('document_id'):
                            existing['score'] = existing.get('score', 0) + chunk.get('score', 0) * 0.5
        
        # Step 3: Rerank and deduplicate
        all_chunks.sort(key=lambda x: x.get('score', 0), reverse=True)
        return all_chunks[:8]  # Return top 8 for better context
    
    def _generate_query_variations(self, query: str) -> List[str]:
        """Generate query variations for multi-query retrieval"""
        variations = [query]  # Original query
        
        # Simple variations (can be enhanced with LLM)
        if "?" in query:
            variations.append(query.replace("?", "").strip())
        
        # Add "what is" variations
        if not query.lower().startswith(("what", "how", "when", "where", "why", "who")):
            variations.append(f"what is {query}")
            variations.append(f"explain {query}")
        
        return variations[:3]  # Limit to 3 variations
    
    def _semantic_search(self, tenant_id: str, query: str, query_variations: List[str]) -> List[Dict]:
        """Semantic search using vector embeddings"""
        try:
            collection_name = f"tenant_{tenant_id}"
            
            # Get or create collection
            try:
                collection = self.chroma_client.get_collection(collection_name)
            except:
                # Collection doesn't exist, return empty (will be created on document upload)
                return []
            
            # Search with query and variations
            all_results = []
            for q in query_variations:
                try:
                    results = collection.query(
                        query_texts=[q],
                        n_results=5
                    )
                    
                    if results['ids'] and len(results['ids'][0]) > 0:
                        for i, doc_id in enumerate(results['ids'][0]):
                            all_results.append({
                                'content': results['documents'][0][i],
                                'source': results['metadatas'][0][i].get('filename', 'Unknown'),
                                'document_id': doc_id,
                                'score': 1.0 - results['distances'][0][i] if 'distances' in results else 0.8,
                                'search_type': 'semantic'
                            })
                except Exception as e:
                    logger.warning(f"Semantic search error: {e}")
                    continue
            
            # Deduplicate and sort
            seen = {}
            for result in all_results:
                key = result['content'][:100]
                if key not in seen or result['score'] > seen[key]['score']:
                    seen[key] = result
            
            return sorted(seen.values(), key=lambda x: x['score'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def _prepare_context(self, chunks: List[Dict]) -> str:
        """Prepare context with better formatting"""
        if not chunks:
            return ""
        
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get('source', 'Unknown')
            content = chunk.get('content', '')
            context_parts.append(f"[Source {i}: {source}]\n{content}")
        
        return "\n\n---\n\n".join(context_parts)
    
    def _build_system_prompt(self, ai_personality: str, response_style: str, company_name: str) -> str:
        """Build human-like, conversational system prompt"""
        personality_traits = {
            "helpful": "warm, friendly, and genuinely interested in helping",
            "professional": "polite, knowledgeable, and confident",
            "casual": "relaxed, friendly, and easy-going",
            "technical": "precise, knowledgeable, and clear",
            "concise": "direct, clear, and to-the-point"
        }
        
        trait = personality_traits.get(ai_personality, "warm and friendly")
        
        return f"""You are a real person helping customers at {company_name}. You're {trait}.

IMPORTANT RULES:
- Respond like a human would - naturally, conversationally, and warmly
- NEVER mention sources, documents, or citations - just answer naturally
- Use "I" and "we" naturally (e.g., "I can help with that!", "We offer...")
- Be engaging and friendly - show personality
- If you don't know something, say so naturally: "I'm not sure about that, but let me help you find out"
- Keep responses conversational and human-like
- Use natural language - avoid robotic phrases
- Show enthusiasm when appropriate
- Answer based ONLY on the context provided, but make it sound natural

Tone: {ai_personality} and human-like. Be yourself - a helpful person, not a chatbot."""
    
    def _build_user_prompt(self, context: str, query: str, company_name: str) -> str:
        """Build natural, conversational user prompt"""
        return f"""A customer just asked: "{query}"

Here's what you know about {company_name}:
{context}

Answer their question naturally, like a helpful person would. Be conversational, friendly, and human. Don't mention sources or documents - just give them a natural, helpful answer."""
    
    async def _call_openrouter_with_retry(self, query: str, context: str, company_name: str, 
                                         ai_personality: str, response_style: str, 
                                         max_retries: int = 3) -> Optional[str]:
        """Call OpenRouter API with retry logic for rate limits (429 errors)"""
        for attempt in range(max_retries):
            try:
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
                                "content": self._build_system_prompt(ai_personality, response_style, company_name)
                            },
                            {
                                "role": "user", 
                                "content": self._build_user_prompt(context, query, company_name)
                            }
                        ],
                        "max_tokens": 400,  # More tokens for natural conversation
                        "temperature": 0.8  # Higher for more natural, human-like responses
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                
                elif response.status_code == 429:
                    # Rate limit - wait with exponential backoff
                    wait_time = (2 ** attempt) + (attempt * 0.5)  # 1s, 2.5s, 5.5s
                    logger.warning(f"Rate limit hit (429). Waiting {wait_time:.1f}s before retry {attempt + 1}/{max_retries}")
                    
                    if attempt < max_retries - 1:
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error("Max retries reached for rate limit")
                        return None
                
                else:
                    # Other error
                    error_text = response.text[:200] if response.text else "Unknown error"
                    logger.error(f"OpenRouter API error {response.status_code}: {error_text}")
                    return None
                    
            except httpx.TimeoutException:
                logger.warning(f"Request timeout on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                return None
            except Exception as e:
                logger.error(f"Error calling OpenRouter API: {e}")
                return None
        
        return None
    
    def _generate_fallback_answer(self, context: str, query: str, company_name: str) -> str:
        """Generate a simple fallback answer when API is unavailable"""
        # Simple keyword-based answer from context
        query_lower = query.lower()
        context_lower = context.lower()
        
        # Find relevant sentences
        sentences = context.split('. ')
        relevant_sentences = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            # Check if sentence contains query words
            query_words = [w for w in query_lower.split() if len(w) > 3]
            matches = sum(1 for word in query_words if word in sentence_lower)
            
            if matches > 0:
                relevant_sentences.append(sentence.strip())
        
        if relevant_sentences:
            answer = '. '.join(relevant_sentences[:2]) + '.'
            return f"Sure! {answer} If you need more details, feel free to ask!"
        else:
            return f"I'd love to help with that! Let me get back to you with more information in just a moment."
    
    def _store_vectors(self, tenant_id: str, filename: str, content: str):
        """Store document chunks as vectors in ChromaDB"""
        try:
            collection_name = f"tenant_{tenant_id}"
            
            # Get or create collection
            try:
                collection = self.chroma_client.get_collection(collection_name)
            except:
                collection = self.chroma_client.create_collection(
                    name=collection_name,
                    metadata={"tenant_id": tenant_id}
                )
            
            # Split content into chunks
            chunks = self.text_splitter.split_text(content)
            
            # Generate embeddings and store
            if chunks:
                embeddings = self.embedding_model.encode(chunks, show_progress_bar=False)
                
                # Prepare data for ChromaDB
                ids = [f"{tenant_id}_{filename}_{i}" for i in range(len(chunks))]
                metadatas = [
                    {
                        "filename": filename,
                        "tenant_id": tenant_id,
                        "chunk_index": i
                    }
                    for i in range(len(chunks))
                ]
                
                collection.add(
                    ids=ids,
                    embeddings=embeddings.tolist(),
                    documents=chunks,
                    metadatas=metadatas
                )
                
                logger.info(f"✅ Stored {len(chunks)} vector chunks for {filename} in ChromaDB")
            
        except Exception as e:
            logger.warning(f"Could not store vectors in ChromaDB: {e}")
            # Continue without vector storage - keyword search will still work
    
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
            
            # Advanced retrieval: Multi-query + Hybrid search
            relevant_chunks = self._advanced_retrieval(tenant_id, query)
            
            if not relevant_chunks:
                return {
                    "answer": f"No relevant information found in {tenant_info.get('company_name', 'your company')}'s documents.",
                    "sources": []
                }
            
            # Prepare enhanced context with better formatting
            context = self._prepare_context(relevant_chunks[:5])  # Use top 5 chunks
            sources = [{"source": chunk['source'], "relevance": chunk.get('score', 0)} for chunk in relevant_chunks[:5]]
            
            # Get tenant-specific AI personality
            ai_personality = tenant_info.get("settings", {}).get("ai_personality", "helpful")
            response_style = tenant_info.get("settings", {}).get("response_style", "concise")
            company_name = tenant_info.get("company_name", "the company")
            
            # Call OpenRouter API with retry logic for rate limits
            answer = await self._call_openrouter_with_retry(
                query=query,
                context=context,
                company_name=company_name,
                ai_personality=ai_personality,
                response_style=response_style
            )
            
            if answer:
                # Return answer without sources for customer-facing responses
                return {"answer": answer, "sources": sources, "tenant_id": tenant_id}
            else:
                # Fallback: Return context-based answer if API fails
                fallback = self._generate_fallback_answer(context, query, company_name)
                return {
                    "answer": fallback,
                    "sources": sources,  # Keep in backend for logging
                    "tenant_id": tenant_id
                }
                
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

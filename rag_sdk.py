"""
Multi-Tenant RAG SDK for Python

This SDK provides a simple interface to interact with the Multi-Tenant RAG API.
It handles authentication, error handling, and provides convenient methods for
all API operations.

Usage:
    from rag_sdk import RAGClient
    
    client = RAGClient("http://localhost:8000", "your_jwt_token")
    
    # Query documents
    result = client.query("What is the main topic?", "company_example_com")
    print(result['answer'])
    
    # Upload documents
    result = client.upload_document("document.pdf", "company_example_com")
    print(f"Uploaded {result['chunks']} chunks")
"""

import requests
import json
from typing import Dict, List, Optional, Union
from pathlib import Path
import time


class RAGError(Exception):
    """Custom exception for RAG API errors"""
    pass


class RAGClient:
    """
    Client for interacting with the Multi-Tenant RAG API
    """
    
    def __init__(self, base_url: str, token: str, timeout: int = 30):
        """
        Initialize the RAG client
        
        Args:
            base_url: Base URL of the RAG API (e.g., "http://localhost:8000")
            token: JWT authentication token
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """
        Make a request to the API with error handling
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            **kwargs: Additional arguments for requests
            
        Returns:
            JSON response data
            
        Raises:
            RAGError: If the request fails
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            
            # Handle different response types
            if response.headers.get('content-type', '').startswith('application/json'):
                data = response.json()
            else:
                data = {'content': response.text}
            
            # Check for errors
            if not response.ok:
                error_msg = data.get('detail', f'HTTP {response.status_code}: {response.reason}')
                raise RAGError(f"API request failed: {error_msg}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            raise RAGError(f"Request failed: {str(e)}")
    
    def health_check(self) -> Dict:
        """
        Check if the API is running
        
        Returns:
            Health status
        """
        return self._make_request('GET', '/healthcheck')
    
    def query(self, question: str, tenant_id: str = "default") -> Dict:
        """
        Send a query to the RAG system
        
        Args:
            question: The question to ask
            tenant_id: Tenant ID (defaults to "default")
            
        Returns:
            Query response with answer and sources
        """
        if tenant_id == "default":
            endpoint = "/query"
            data = {"query": question}
        else:
            endpoint = "/query/tenant"
            data = {"query": question, "tenant_id": tenant_id}
        
        return self._make_request('POST', endpoint, json=data)
    
    def upload_document(self, file_path: Union[str, Path], tenant_id: str = "default") -> Dict:
        """
        Upload a document to the RAG system
        
        Args:
            file_path: Path to the file to upload
            tenant_id: Tenant ID (defaults to "default")
            
        Returns:
            Upload response with chunk count and status
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise RAGError(f"File not found: {file_path}")
        
        if tenant_id == "default":
            endpoint = "/upload"
        else:
            endpoint = f"/upload/tenant?tenant_id={tenant_id}"
        
        # Remove Content-Type header for file upload
        headers = {'Authorization': f'Bearer {self.token}'}
        
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = self.session.post(
                f"{self.base_url}{endpoint}",
                headers=headers,
                files=files,
                timeout=self.timeout
            )
        
        if not response.ok:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'HTTP {response.status_code}: {response.reason}')
            except:
                error_msg = f'HTTP {response.status_code}: {response.reason}'
            raise RAGError(f"Upload failed: {error_msg}")
        
        return response.json()
    
    def get_tenants(self) -> Dict:
        """
        Get list of all tenants
        
        Returns:
            List of tenants with their information
        """
        return self._make_request('GET', '/tenants/')
    
    def get_tenant(self, tenant_id: str) -> Dict:
        """
        Get information about a specific tenant
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Tenant information
        """
        return self._make_request('GET', f'/tenants/{tenant_id}')
    
    def create_tenant(self, tenant_data: Dict) -> Dict:
        """
        Create a new tenant
        
        Args:
            tenant_data: Tenant information dictionary
            
        Returns:
            Created tenant information
        """
        return self._make_request('POST', '/tenants/register', json=tenant_data)
    
    def update_tenant(self, tenant_id: str, updates: Dict) -> Dict:
        """
        Update tenant configuration
        
        Args:
            tenant_id: Tenant ID
            updates: Dictionary of fields to update
            
        Returns:
            Update confirmation
        """
        return self._make_request('PUT', f'/tenants/{tenant_id}', json=updates)
    
    def delete_tenant(self, tenant_id: str) -> Dict:
        """
        Delete a tenant and all associated data
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Deletion confirmation
        """
        return self._make_request('DELETE', f'/tenants/{tenant_id}')
    
    def get_tenant_documents(self, tenant_id: str) -> Dict:
        """
        Get all documents for a tenant
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            List of documents with metadata
        """
        return self._make_request('GET', f'/tenants/{tenant_id}/documents')
    
    def delete_document(self, tenant_id: str, document_id: str) -> Dict:
        """
        Delete a specific document
        
        Args:
            tenant_id: Tenant ID
            document_id: Document ID
            
        Returns:
            Deletion confirmation
        """
        return self._make_request('DELETE', f'/tenants/{tenant_id}/documents/{document_id}')
    
    def get_collection_info(self, tenant_id: str = "default") -> Dict:
        """
        Get collection information for a tenant
        
        Args:
            tenant_id: Tenant ID (defaults to "default")
            
        Returns:
            Collection information and statistics
        """
        return self._make_request('GET', f'/collection-info?tenant_id={tenant_id}')
    
    def get_document_count(self, tenant_id: str = "default") -> Dict:
        """
        Get document count for a tenant
        
        Args:
            tenant_id: Tenant ID (defaults to "default")
            
        Returns:
            Document count information
        """
        return self._make_request('GET', f'/document-count?tenant_id={tenant_id}')
    
    def get_tenant_stats(self, tenant_id: str) -> Dict:
        """
        Get comprehensive statistics for a tenant
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Tenant statistics
        """
        return self._make_request('GET', f'/tenants/{tenant_id}/stats')
    
    def bulk_upload(self, file_paths: List[Union[str, Path]], tenant_id: str = "default") -> List[Dict]:
        """
        Upload multiple documents
        
        Args:
            file_paths: List of file paths to upload
            tenant_id: Tenant ID (defaults to "default")
            
        Returns:
            List of upload results
        """
        results = []
        for file_path in file_paths:
            try:
                result = self.upload_document(file_path, tenant_id)
                results.append({
                    'file': str(file_path),
                    'success': True,
                    'result': result
                })
            except RAGError as e:
                results.append({
                    'file': str(file_path),
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    def search_documents(self, query: str, tenant_id: str = "default") -> Dict:
        """
        Search through documents (alias for query method)
        
        Args:
            query: Search query
            tenant_id: Tenant ID (defaults to "default")
            
        Returns:
            Search results
        """
        return self.query(query, tenant_id)
    
    def get_token(self) -> str:
        """
        Get a new JWT token from the API
        
        Returns:
            JWT token
        """
        # Temporarily remove auth header to get token
        original_headers = self.session.headers.copy()
        self.session.headers.pop('Authorization', None)
        
        try:
            response = self._make_request('GET', '/get-token')
            return response['token']
        finally:
            # Restore original headers
            self.session.headers.update(original_headers)


class RAGManager:
    """
    High-level manager for RAG operations with multiple tenants
    """
    
    def __init__(self, base_url: str, token: str):
        """
        Initialize the RAG manager
        
        Args:
            base_url: Base URL of the RAG API
            token: JWT authentication token
        """
        self.client = RAGClient(base_url, token)
        self._tenants_cache = None
        self._cache_time = 0
        self._cache_duration = 300  # 5 minutes
    
    def get_tenant_by_domain(self, domain: str) -> Optional[Dict]:
        """
        Find a tenant by domain name
        
        Args:
            domain: Company domain
            
        Returns:
            Tenant information or None if not found
        """
        tenants = self.get_tenants()
        for tenant in tenants.get('tenants', []):
            if tenant.get('company_domain') == domain:
                return tenant
        return None
    
    def get_tenants(self, use_cache: bool = True) -> Dict:
        """
        Get tenants with caching
        
        Args:
            use_cache: Whether to use cached data
            
        Returns:
            List of tenants
        """
        current_time = time.time()
        
        if (use_cache and self._tenants_cache and 
            current_time - self._cache_time < self._cache_duration):
            return self._tenants_cache
        
        self._tenants_cache = self.client.get_tenants()
        self._cache_time = current_time
        return self._tenants_cache
    
    def create_tenant_from_domain(self, domain: str, company_name: str, 
                                 email: str, **kwargs) -> Dict:
        """
        Create a tenant from domain information
        
        Args:
            domain: Company domain
            company_name: Company name
            email: Company email
            **kwargs: Additional tenant data
            
        Returns:
            Created tenant information
        """
        tenant_data = {
            'company_name': company_name,
            'company_domain': domain,
            'company_email': email,
            'plan': 'basic',
            'max_documents': 100,
            'max_queries_per_day': 1000,
            'ai_personality': 'helpful',
            'response_style': 'concise',
            'primary_color': '#007bff',
            **kwargs
        }
        
        result = self.client.create_tenant(tenant_data)
        
        # Invalidate cache
        self._tenants_cache = None
        
        return result
    
    def setup_tenant_documents(self, tenant_id: str, document_paths: List[Union[str, Path]]) -> Dict:
        """
        Set up a tenant with initial documents
        
        Args:
            tenant_id: Tenant ID
            document_paths: List of document paths to upload
            
        Returns:
            Setup summary
        """
        results = self.client.bulk_upload(document_paths, tenant_id)
        
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        return {
            'tenant_id': tenant_id,
            'total_files': len(document_paths),
            'successful_uploads': len(successful),
            'failed_uploads': len(failed),
            'results': results
        }
    
    def get_tenant_summary(self, tenant_id: str) -> Dict:
        """
        Get a comprehensive summary of a tenant
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Tenant summary with all relevant information
        """
        try:
            tenant_info = self.client.get_tenant(tenant_id)
            collection_info = self.client.get_collection_info(tenant_id)
            documents = self.client.get_tenant_documents(tenant_id)
            stats = self.client.get_tenant_stats(tenant_id)
            
            return {
                'tenant_info': tenant_info,
                'collection_info': collection_info,
                'documents': documents,
                'stats': stats
            }
        except RAGError as e:
            return {'error': str(e)}


# Convenience functions for quick operations
def quick_query(base_url: str, token: str, question: str, tenant_id: str = "default") -> str:
    """
    Quick function to ask a question and get just the answer
    
    Args:
        base_url: RAG API base URL
        token: JWT token
        question: Question to ask
        tenant_id: Tenant ID
        
    Returns:
        Answer string
    """
    client = RAGClient(base_url, token)
    result = client.query(question, tenant_id)
    return result.get('answer', 'No answer available')


def quick_upload(base_url: str, token: str, file_path: str, tenant_id: str = "default") -> int:
    """
    Quick function to upload a document and get chunk count
    
    Args:
        base_url: RAG API base URL
        token: JWT token
        file_path: Path to file
        tenant_id: Tenant ID
        
    Returns:
        Number of chunks created
    """
    client = RAGClient(base_url, token)
    result = client.upload_document(file_path, tenant_id)
    return result.get('chunks', 0)


# Example usage
if __name__ == "__main__":
    # Initialize client
    client = RAGClient("http://localhost:8000", "your_jwt_token")
    
    # Health check
    print("Health check:", client.health_check())
    
    # Query a document
    result = client.query("What is the main topic?", "company_example_com")
    print("Query result:", result['answer'])
    
    # Upload a document
    upload_result = client.upload_document("document.pdf", "company_example_com")
    print(f"Uploaded {upload_result['chunks']} chunks")
    
    # Get tenant information
    tenants = client.get_tenants()
    print(f"Found {tenants['total_count']} tenants")
    
    # Quick operations
    answer = quick_query("http://localhost:8000", "your_jwt_token", "What is AI?")
    print("Quick answer:", answer)
    
    chunks = quick_upload("http://localhost:8000", "your_jwt_token", "document.pdf")
    print(f"Quick upload: {chunks} chunks")

# Multi-Tenant RAG API Documentation

## Overview
This document provides comprehensive API documentation for the Multi-Tenant RAG (Retrieval-Augmented Generation) system. The API allows you to manage multiple tenants, upload documents, and query them using AI-powered responses.

## Base URL
```
http://localhost:8000
```

## Authentication
All API endpoints require JWT authentication using the `Authorization` header:
```
Authorization: Bearer YOUR_JWT_TOKEN
```

### Getting a Token
```bash
curl -X GET "http://localhost:8000/get-token"
```

## API Endpoints

### 1. Health Check
**GET** `/healthcheck`

Check if the API is running.

**Response:**
```json
{
  "status": "ok"
}
```

### 2. Chat/Query Endpoints

#### 2.1 Query Default Tenant
**POST** `/query`

Send a query to the default tenant's RAG system.

**Request Body:**
```json
{
  "query": "What is the main topic of the document?",
  "tenant_id": "default"
}
```

**Response:**
```json
{
  "answer": "The main topic is about artificial intelligence and machine learning...",
  "sources": [
    {"source": "document.pdf"},
    {"source": "report.txt"}
  ]
}
```

#### 2.2 Query Specific Tenant
**POST** `/query/tenant`

Send a query to a specific tenant's RAG system.

**Request Body:**
```json
{
  "query": "What is the main topic?",
  "tenant_id": "company_example_com"
}
```

**Response:**
```json
{
  "answer": "Based on your company's documents, the main topic is...",
  "sources": [
    {"source": "company_handbook.pdf"},
    {"source": "policies.txt"}
  ],
  "tenant_id": "company_example_com"
}
```

### 3. Document Upload Endpoints

#### 3.1 Upload to Default Tenant
**POST** `/upload`

Upload a document to the default tenant.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: Form data with `file` field

**Example:**
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf"
```

**Response:**
```json
{
  "chunks": 15,
  "status": "success",
  "message": "Document processed successfully"
}
```

#### 3.2 Upload to Specific Tenant
**POST** `/upload/tenant`

Upload a document to a specific tenant.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Query Parameter: `tenant_id`
- Body: Form data with `file` field

**Example:**
```bash
curl -X POST "http://localhost:8000/upload/tenant?tenant_id=company_example_com" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf"
```

**Response:**
```json
{
  "chunks": 15,
  "status": "success",
  "message": "Document processed successfully for tenant company_example_com",
  "tenant_id": "company_example_com",
  "filename": "document.pdf",
  "file_type": "pdf"
}
```

### 4. Tenant Management Endpoints

#### 4.1 List All Tenants
**GET** `/tenants/`

Get a list of all tenants in the system.

**Response:**
```json
{
  "tenants": [
    {
      "tenant_id": "company_example_com",
      "company_name": "Example Company",
      "company_domain": "example.com",
      "company_email": "admin@example.com",
      "api_key": "tenant_api_key_here",
      "status": "active",
      "plan": "basic",
      "created_at": "2024-01-15T10:30:00Z",
      "document_count": 5,
      "total_queries": 150
    }
  ],
  "total_count": 1
}
```

#### 4.2 Get Specific Tenant
**GET** `/tenants/{tenant_id}`

Get detailed information about a specific tenant.

**Response:**
```json
{
  "tenant_id": "company_example_com",
  "company_name": "Example Company",
  "company_domain": "example.com",
  "company_email": "admin@example.com",
  "api_key": "tenant_api_key_here",
  "status": "active",
  "plan": "basic",
  "created_at": "2024-01-15T10:30:00Z",
  "document_count": 5,
  "total_queries": 150
}
```

#### 4.3 Register New Tenant
**POST** `/tenants/register`

Register a new tenant in the system.

**Request Body:**
```json
{
  "company_name": "New Company",
  "company_domain": "newcompany.com",
  "company_email": "admin@newcompany.com",
  "company_phone": "+1-555-0123",
  "plan": "basic",
  "max_documents": 100,
  "max_queries_per_day": 1000,
  "ai_personality": "helpful",
  "response_style": "concise",
  "primary_color": "#007bff",
  "company_description": "A new company using our RAG system"
}
```

**Response:**
```json
{
  "tenant_id": "newcompany_com",
  "company_name": "New Company",
  "company_domain": "newcompany.com",
  "company_email": "admin@newcompany.com",
  "api_key": "generated_api_key_here",
  "status": "active",
  "plan": "basic",
  "created_at": "2024-01-15T10:30:00Z",
  "document_count": 0,
  "total_queries": 0
}
```

#### 4.4 Update Tenant
**PUT** `/tenants/{tenant_id}`

Update tenant configuration.

**Request Body:**
```json
{
  "company_name": "Updated Company Name",
  "plan": "pro",
  "ai_personality": "professional",
  "response_style": "detailed"
}
```

**Response:**
```json
{
  "message": "Tenant company_example_com updated successfully"
}
```

#### 4.5 Delete Tenant
**DELETE** `/tenants/{tenant_id}`

Delete a tenant and all associated data.

**Response:**
```json
{
  "message": "Tenant company_example_com deleted successfully"
}
```

### 5. Document Management Endpoints

#### 5.1 Get Tenant Documents
**GET** `/tenants/{tenant_id}/documents`

Get all documents for a specific tenant.

**Response:**
```json
{
  "tenant_id": "company_example_com",
  "documents": [
    {
      "document_id": "doc_123",
      "filename": "handbook.pdf",
      "file_type": "pdf",
      "uploaded_at": "2024-01-15T10:30:00Z",
      "chunks": [
        {
          "content": "Document content here...",
          "source": "handbook.pdf"
        }
      ]
    }
  ],
  "total_count": 1
}
```

#### 5.2 Delete Document
**DELETE** `/tenants/{tenant_id}/documents/{document_id}`

Delete a specific document from a tenant.

**Response:**
```json
{
  "message": "Document doc_123 deleted successfully from tenant company_example_com"
}
```

### 6. Analytics and Statistics

#### 6.1 Get Collection Info
**GET** `/collection-info`

Get information about the current tenant's document collection.

**Query Parameters:**
- `tenant_id` (optional): Tenant ID (defaults to "default")

**Response:**
```json
{
  "tenant_id": "company_example_com",
  "company_name": "Example Company",
  "document_count": 5,
  "storage_type": "tenant_specific",
  "llm_provider": "openrouter",
  "model": "meta-llama/llama-3.2-3b-instruct:free",
  "plan": "basic",
  "status": "active",
  "total_queries": 150,
  "queries_today": 12
}
```

#### 6.2 Get Document Count
**GET** `/document-count`

Get the number of documents in the collection.

**Query Parameters:**
- `tenant_id` (optional): Tenant ID (defaults to "default")

**Response:**
```json
{
  "document_count": 5,
  "tenant_id": "company_example_com"
}
```

#### 6.3 Get Tenant Statistics
**GET** `/tenants/{tenant_id}/stats`

Get comprehensive statistics for a tenant.

**Response:**
```json
{
  "tenant_info": {
    "tenant_id": "company_example_com",
    "company_name": "Example Company",
    "status": "active",
    "plan": "basic"
  },
  "total_documents": 5,
  "total_queries": 150,
  "queries_today": 12,
  "popular_queries": [
    "What is the company policy?",
    "How do I submit a request?"
  ],
  "document_types": {
    "pdf": 3,
    "text": 2
  }
}
```

## Supported File Types

The system supports the following file types for document upload:

- **PDF** (.pdf) - Extracts text from PDF documents
- **Text** (.txt, .md) - Plain text and markdown files
- **JSON** (.json) - JSON data files
- **CSV** (.csv) - Comma-separated value files

## Error Handling

All endpoints return appropriate HTTP status codes and error messages:

### Common Error Responses

#### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

#### 404 Not Found
```json
{
  "detail": "Tenant company_example_com not found"
}
```

#### 400 Bad Request
```json
{
  "detail": "Tenant with domain example.com already exists"
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Internal server error: Error message here"
}
```

## Rate Limiting

The system implements rate limiting based on tenant plans:

- **Basic Plan**: 1000 queries per day
- **Pro Plan**: 5000 queries per day
- **Enterprise Plan**: Unlimited queries

## Integration Examples

### Python Integration

```python
import requests
import json

class RAGClient:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def query(self, question, tenant_id="default"):
        url = f"{self.base_url}/query"
        if tenant_id != "default":
            url = f"{self.base_url}/query/tenant"
        
        data = {"query": question}
        if tenant_id != "default":
            data["tenant_id"] = tenant_id
        
        response = requests.post(url, headers=self.headers, json=data)
        return response.json()
    
    def upload_document(self, file_path, tenant_id="default"):
        url = f"{self.base_url}/upload"
        if tenant_id != "default":
            url = f"{self.base_url}/upload/tenant?tenant_id={tenant_id}"
        
        with open(file_path, 'rb') as f:
            files = {'file': f}
            headers = {'Authorization': self.headers['Authorization']}
            response = requests.post(url, headers=headers, files=files)
        
        return response.json()
    
    def get_tenants(self):
        response = requests.get(f"{self.base_url}/tenants/", headers=self.headers)
        return response.json()
    
    def create_tenant(self, tenant_data):
        response = requests.post(
            f"{self.base_url}/tenants/register",
            headers=self.headers,
            json=tenant_data
        )
        return response.json()

# Usage example
client = RAGClient("http://localhost:8000", "your_jwt_token")

# Query a document
result = client.query("What is the main topic?", "company_example_com")
print(result['answer'])

# Upload a document
upload_result = client.upload_document("document.pdf", "company_example_com")
print(f"Uploaded {upload_result['chunks']} chunks")
```

### JavaScript/Node.js Integration

```javascript
class RAGClient {
    constructor(baseUrl, token) {
        this.baseUrl = baseUrl;
        this.token = token;
    }
    
    async query(question, tenantId = "default") {
        const url = tenantId === "default" 
            ? `${this.baseUrl}/query`
            : `${this.baseUrl}/query/tenant`;
        
        const body = { query: question };
        if (tenantId !== "default") {
            body.tenant_id = tenantId;
        }
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(body)
        });
        
        return await response.json();
    }
    
    async uploadDocument(file, tenantId = "default") {
        const url = tenantId === "default"
            ? `${this.baseUrl}/upload`
            : `${this.baseUrl}/upload/tenant?tenant_id=${tenantId}`;
        
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`
            },
            body: formData
        });
        
        return await response.json();
    }
    
    async getTenants() {
        const response = await fetch(`${this.baseUrl}/tenants/`, {
            headers: {
                'Authorization': `Bearer ${this.token}`
            }
        });
        
        return await response.json();
    }
}

// Usage example
const client = new RAGClient("http://localhost:8000", "your_jwt_token");

// Query a document
const result = await client.query("What is the main topic?", "company_example_com");
console.log(result.answer);

// Upload a document
const fileInput = document.getElementById('fileInput');
const file = fileInput.files[0];
const uploadResult = await client.uploadDocument(file, "company_example_com");
console.log(`Uploaded ${uploadResult.chunks} chunks`);
```

### cURL Examples

#### Query a document
```bash
curl -X POST "http://localhost:8000/query/tenant" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the company policy on remote work?",
    "tenant_id": "company_example_com"
  }'
```

#### Upload a document
```bash
curl -X POST "http://localhost:8000/upload/tenant?tenant_id=company_example_com" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@company_handbook.pdf"
```

#### Get tenant information
```bash
curl -X GET "http://localhost:8000/tenants/company_example_com" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Create a new tenant
```bash
curl -X POST "http://localhost:8000/tenants/register" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "New Company",
    "company_domain": "newcompany.com",
    "company_email": "admin@newcompany.com",
    "plan": "basic",
    "ai_personality": "professional",
    "response_style": "concise"
  }'
```

## Best Practices

1. **Authentication**: Always include the JWT token in the Authorization header
2. **Error Handling**: Check HTTP status codes and handle errors appropriately
3. **Rate Limiting**: Monitor your query usage to stay within plan limits
4. **File Types**: Use supported file types for optimal document processing
5. **Tenant Isolation**: Always specify the correct tenant_id for multi-tenant operations
6. **Document Size**: Keep documents reasonably sized for better processing performance

## WebSocket Support (Future)

The system is designed to support WebSocket connections for real-time chat functionality. This will be available in future updates.

## Support

For technical support or questions about the API, please refer to the system documentation or contact the development team.

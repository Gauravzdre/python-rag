# Multi-Tenant RAG Integration Guide

This guide provides step-by-step instructions for integrating the Multi-Tenant RAG system into your applications using various programming languages and frameworks.

## Table of Contents
1. [Quick Start](#quick-start)
2. [Python Integration](#python-integration)
3. [JavaScript/Node.js Integration](#javascriptnodejs-integration)
4. [Java Integration](#java-integration)
5. [C# Integration](#c-integration)
6. [PHP Integration](#php-integration)
7. [Go Integration](#go-integration)
8. [Ruby Integration](#ruby-integration)
9. [Webhook Integration](#webhook-integration)
10. [Best Practices](#best-practices)

## Quick Start

### 1. Get Authentication Token
```bash
curl -X GET "http://localhost:8000/get-token"
```

### 2. Test Connection
```bash
curl -X GET "http://localhost:8000/healthcheck" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Upload a Document
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf"
```

### 4. Query Documents
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the main topic?"}'
```

## Python Integration

### Using the SDK (Recommended)

```python
from rag_sdk import RAGClient, RAGManager

# Initialize client
client = RAGClient("http://localhost:8000", "your_jwt_token")

# Query documents
result = client.query("What is the company policy?", "company_example_com")
print(result['answer'])

# Upload document
upload_result = client.upload_document("handbook.pdf", "company_example_com")
print(f"Uploaded {upload_result['chunks']} chunks")

# Create tenant
tenant_data = {
    "company_name": "New Company",
    "company_domain": "newcompany.com",
    "company_email": "admin@newcompany.com",
    "plan": "basic"
}
new_tenant = client.create_tenant(tenant_data)
print(f"Created tenant: {new_tenant['tenant_id']}")
```

### Using Requests Library

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
        response.raise_for_status()
        return response.json()
    
    def upload_document(self, file_path, tenant_id="default"):
        url = f"{self.base_url}/upload"
        if tenant_id != "default":
            url = f"{self.base_url}/upload/tenant?tenant_id={tenant_id}"
        
        with open(file_path, 'rb') as f:
            files = {'file': f}
            headers = {'Authorization': self.headers['Authorization']}
            response = requests.post(url, headers=headers, files=files)
        
        response.raise_for_status()
        return response.json()

# Usage
client = RAGClient("http://localhost:8000", "your_jwt_token")
result = client.query("What is AI?", "company_example_com")
print(result['answer'])
```

### Flask Integration

```python
from flask import Flask, request, jsonify
from rag_sdk import RAGClient

app = Flask(__name__)
rag_client = RAGClient("http://localhost:8000", "your_jwt_token")

@app.route('/ask', methods=['POST'])
def ask_question():
    data = request.json
    question = data.get('question')
    tenant_id = data.get('tenant_id', 'default')
    
    try:
        result = rag_client.query(question, tenant_id)
        return jsonify({
            'success': True,
            'answer': result['answer'],
            'sources': result.get('sources', [])
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/upload', methods=['POST'])
def upload_document():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    tenant_id = request.form.get('tenant_id', 'default')
    
    try:
        # Save file temporarily
        file_path = f"/tmp/{file.filename}"
        file.save(file_path)
        
        result = rag_client.upload_document(file_path, tenant_id)
        return jsonify({
            'success': True,
            'chunks': result['chunks'],
            'message': result['message']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
```

### Django Integration

```python
# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from rag_sdk import RAGClient

rag_client = RAGClient("http://localhost:8000", "your_jwt_token")

@csrf_exempt
@require_http_methods(["POST"])
def ask_question(request):
    try:
        data = json.loads(request.body)
        question = data.get('question')
        tenant_id = data.get('tenant_id', 'default')
        
        result = rag_client.query(question, tenant_id)
        
        return JsonResponse({
            'success': True,
            'answer': result['answer'],
            'sources': result.get('sources', [])
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def upload_document(request):
    try:
        file = request.FILES.get('file')
        tenant_id = request.POST.get('tenant_id', 'default')
        
        if not file:
            return JsonResponse({'error': 'No file provided'}, status=400)
        
        # Save file temporarily
        file_path = f"/tmp/{file.name}"
        with open(file_path, 'wb') as f:
            for chunk in file.chunks():
                f.write(chunk)
        
        result = rag_client.upload_document(file_path, tenant_id)
        
        return JsonResponse({
            'success': True,
            'chunks': result['chunks'],
            'message': result['message']
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
```

## JavaScript/Node.js Integration

### Using Fetch API

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
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
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
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    async getTenants() {
        const response = await fetch(`${this.baseUrl}/tenants/`, {
            headers: {
                'Authorization': `Bearer ${this.token}`
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    }
}

// Usage
const client = new RAGClient("http://localhost:8000", "your_jwt_token");

// Query documents
const result = await client.query("What is the main topic?", "company_example_com");
console.log(result.answer);

// Upload document
const fileInput = document.getElementById('fileInput');
const file = fileInput.files[0];
const uploadResult = await client.uploadDocument(file, "company_example_com");
console.log(`Uploaded ${uploadResult.chunks} chunks`);
```

### Express.js Integration

```javascript
const express = require('express');
const multer = require('multer');
const fetch = require('node-fetch');
const app = express();

const upload = multer({ dest: 'uploads/' });
const RAG_BASE_URL = 'http://localhost:8000';
const RAG_TOKEN = 'your_jwt_token';

app.use(express.json());

// Query endpoint
app.post('/ask', async (req, res) => {
    try {
        const { question, tenant_id = 'default' } = req.body;
        
        const url = tenant_id === 'default' 
            ? `${RAG_BASE_URL}/query`
            : `${RAG_BASE_URL}/query/tenant`;
        
        const body = { query: question };
        if (tenant_id !== 'default') {
            body.tenant_id = tenant_id;
        }
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${RAG_TOKEN}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(body)
        });
        
        const result = await response.json();
        
        res.json({
            success: true,
            answer: result.answer,
            sources: result.sources || []
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Upload endpoint
app.post('/upload', upload.single('file'), async (req, res) => {
    try {
        const { tenant_id = 'default' } = req.body;
        const file = req.file;
        
        if (!file) {
            return res.status(400).json({ error: 'No file provided' });
        }
        
        const url = tenant_id === 'default'
            ? `${RAG_BASE_URL}/upload`
            : `${RAG_BASE_URL}/upload/tenant?tenant_id=${tenant_id}`;
        
        const FormData = require('form-data');
        const form = new FormData();
        form.append('file', require('fs').createReadStream(file.path));
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${RAG_TOKEN}`,
                ...form.getHeaders()
            },
            body: form
        });
        
        const result = await response.json();
        
        res.json({
            success: true,
            chunks: result.chunks,
            message: result.message
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

app.listen(3000, () => {
    console.log('Server running on port 3000');
});
```

### React Integration

```jsx
import React, { useState } from 'react';

const RAGComponent = () => {
    const [question, setQuestion] = useState('');
    const [answer, setAnswer] = useState('');
    const [loading, setLoading] = useState(false);
    const [tenantId, setTenantId] = useState('default');

    const askQuestion = async () => {
        if (!question.trim()) return;
        
        setLoading(true);
        try {
            const response = await fetch('/api/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question: question,
                    tenant_id: tenantId
                })
            });
            
            const data = await response.json();
            if (data.success) {
                setAnswer(data.answer);
            } else {
                setAnswer(`Error: ${data.error}`);
            }
        } catch (error) {
            setAnswer(`Error: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    const uploadFile = async (event) => {
        const file = event.target.files[0];
        if (!file) return;
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('tenant_id', tenantId);
        
        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            if (data.success) {
                alert(`Uploaded ${data.chunks} chunks successfully!`);
            } else {
                alert(`Upload failed: ${data.error}`);
            }
        } catch (error) {
            alert(`Upload error: ${error.message}`);
        }
    };

    return (
        <div>
            <h2>RAG Chat Interface</h2>
            
            <div>
                <label>Tenant ID:</label>
                <input
                    type="text"
                    value={tenantId}
                    onChange={(e) => setTenantId(e.target.value)}
                    placeholder="Enter tenant ID"
                />
            </div>
            
            <div>
                <label>Upload Document:</label>
                <input type="file" onChange={uploadFile} />
            </div>
            
            <div>
                <label>Ask a Question:</label>
                <input
                    type="text"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="Enter your question"
                />
                <button onClick={askQuestion} disabled={loading}>
                    {loading ? 'Asking...' : 'Ask'}
                </button>
            </div>
            
            {answer && (
                <div>
                    <h3>Answer:</h3>
                    <p>{answer}</p>
                </div>
            )}
        </div>
    );
};

export default RAGComponent;
```

## Java Integration

### Using Spring Boot

```java
@RestController
@RequestMapping("/api/rag")
public class RAGController {
    
    private final String RAG_BASE_URL = "http://localhost:8000";
    private final String RAG_TOKEN = "your_jwt_token";
    
    @Autowired
    private RestTemplate restTemplate;
    
    @PostMapping("/ask")
    public ResponseEntity<Map<String, Object>> askQuestion(@RequestBody Map<String, String> request) {
        try {
            String question = request.get("question");
            String tenantId = request.getOrDefault("tenant_id", "default");
            
            String url = tenantId.equals("default") 
                ? RAG_BASE_URL + "/query"
                : RAG_BASE_URL + "/query/tenant";
            
            Map<String, Object> body = new HashMap<>();
            body.put("query", question);
            if (!tenantId.equals("default")) {
                body.put("tenant_id", tenantId);
            }
            
            HttpHeaders headers = new HttpHeaders();
            headers.set("Authorization", "Bearer " + RAG_TOKEN);
            headers.set("Content-Type", "application/json");
            
            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(body, headers);
            ResponseEntity<Map> response = restTemplate.postForEntity(url, entity, Map.class);
            
            Map<String, Object> result = response.getBody();
            
            return ResponseEntity.ok(Map.of(
                "success", true,
                "answer", result.get("answer"),
                "sources", result.getOrDefault("sources", new ArrayList<>())
            ));
            
        } catch (Exception e) {
            return ResponseEntity.status(500).body(Map.of(
                "success", false,
                "error", e.getMessage()
            ));
        }
    }
    
    @PostMapping("/upload")
    public ResponseEntity<Map<String, Object>> uploadDocument(
            @RequestParam("file") MultipartFile file,
            @RequestParam(value = "tenant_id", defaultValue = "default") String tenantId) {
        
        try {
            String url = tenantId.equals("default")
                ? RAG_BASE_URL + "/upload"
                : RAG_BASE_URL + "/upload/tenant?tenant_id=" + tenantId;
            
            HttpHeaders headers = new HttpHeaders();
            headers.set("Authorization", "Bearer " + RAG_TOKEN);
            headers.setContentType(MediaType.MULTIPART_FORM_DATA);
            
            MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
            body.add("file", file.getResource());
            
            HttpEntity<MultiValueMap<String, Object>> entity = new HttpEntity<>(body, headers);
            ResponseEntity<Map> response = restTemplate.postForEntity(url, entity, Map.class);
            
            Map<String, Object> result = response.getBody();
            
            return ResponseEntity.ok(Map.of(
                "success", true,
                "chunks", result.get("chunks"),
                "message", result.get("message")
            ));
            
        } catch (Exception e) {
            return ResponseEntity.status(500).body(Map.of(
                "success", false,
                "error", e.getMessage()
            ));
        }
    }
}
```

### Using OkHttp

```java
import okhttp3.*;
import com.fasterxml.jackson.databind.ObjectMapper;

public class RAGClient {
    private final String baseUrl;
    private final String token;
    private final OkHttpClient client;
    private final ObjectMapper objectMapper;
    
    public RAGClient(String baseUrl, String token) {
        this.baseUrl = baseUrl;
        this.token = token;
        this.client = new OkHttpClient();
        this.objectMapper = new ObjectMapper();
    }
    
    public Map<String, Object> query(String question, String tenantId) throws IOException {
        String url = tenantId.equals("default") 
            ? baseUrl + "/query"
            : baseUrl + "/query/tenant";
        
        Map<String, Object> body = new HashMap<>();
        body.put("query", question);
        if (!tenantId.equals("default")) {
            body.put("tenant_id", tenantId);
        }
        
        RequestBody requestBody = RequestBody.create(
            objectMapper.writeValueAsString(body),
            MediaType.get("application/json")
        );
        
        Request request = new Request.Builder()
            .url(url)
            .post(requestBody)
            .addHeader("Authorization", "Bearer " + token)
            .build();
        
        try (Response response = client.newCall(request).execute()) {
            if (!response.isSuccessful()) {
                throw new IOException("Unexpected code " + response);
            }
            
            return objectMapper.readValue(response.body().string(), Map.class);
        }
    }
    
    public Map<String, Object> uploadDocument(File file, String tenantId) throws IOException {
        String url = tenantId.equals("default")
            ? baseUrl + "/upload"
            : baseUrl + "/upload/tenant?tenant_id=" + tenantId;
        
        RequestBody fileBody = RequestBody.create(file, MediaType.get("application/octet-stream"));
        RequestBody requestBody = new MultipartBody.Builder()
            .setType(MultipartBody.FORM)
            .addFormDataPart("file", file.getName(), fileBody)
            .build();
        
        Request request = new Request.Builder()
            .url(url)
            .post(requestBody)
            .addHeader("Authorization", "Bearer " + token)
            .build();
        
        try (Response response = client.newCall(request).execute()) {
            if (!response.isSuccessful()) {
                throw new IOException("Unexpected code " + response);
            }
            
            return objectMapper.readValue(response.body().string(), Map.class);
        }
    }
}
```

## C# Integration

### Using HttpClient

```csharp
using System;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

public class RAGClient
{
    private readonly HttpClient _httpClient;
    private readonly string _baseUrl;
    private readonly string _token;
    
    public RAGClient(string baseUrl, string token)
    {
        _baseUrl = baseUrl;
        _token = token;
        _httpClient = new HttpClient();
        _httpClient.DefaultRequestHeaders.Add("Authorization", $"Bearer {token}");
    }
    
    public async Task<QueryResponse> QueryAsync(string question, string tenantId = "default")
    {
        var url = tenantId == "default" 
            ? $"{_baseUrl}/query"
            : $"{_baseUrl}/query/tenant";
        
        var requestBody = new
        {
            query = question,
            tenant_id = tenantId != "default" ? tenantId : null
        };
        
        var json = JsonSerializer.Serialize(requestBody);
        var content = new StringContent(json, Encoding.UTF8, "application/json");
        
        var response = await _httpClient.PostAsync(url, content);
        response.EnsureSuccessStatusCode();
        
        var responseJson = await response.Content.ReadAsStringAsync();
        return JsonSerializer.Deserialize<QueryResponse>(responseJson);
    }
    
    public async Task<UploadResponse> UploadDocumentAsync(string filePath, string tenantId = "default")
    {
        var url = tenantId == "default"
            ? $"{_baseUrl}/upload"
            : $"{_baseUrl}/upload/tenant?tenant_id={tenantId}";
        
        using var form = new MultipartFormDataContent();
        using var fileContent = new ByteArrayContent(await File.ReadAllBytesAsync(filePath));
        fileContent.Headers.ContentType = new System.Net.Http.Headers.MediaTypeHeaderValue("application/octet-stream");
        form.Add(fileContent, "file", Path.GetFileName(filePath));
        
        var response = await _httpClient.PostAsync(url, form);
        response.EnsureSuccessStatusCode();
        
        var responseJson = await response.Content.ReadAsStringAsync();
        return JsonSerializer.Deserialize<UploadResponse>(responseJson);
    }
}

public class QueryResponse
{
    public string Answer { get; set; }
    public List<Source> Sources { get; set; }
}

public class Source
{
    public string Source { get; set; }
}

public class UploadResponse
{
    public int Chunks { get; set; }
    public string Status { get; set; }
    public string Message { get; set; }
}
```

### ASP.NET Core Integration

```csharp
[ApiController]
[Route("api/[controller]")]
public class RAGController : ControllerBase
{
    private readonly RAGClient _ragClient;
    
    public RAGController(IConfiguration configuration)
    {
        var baseUrl = configuration["RAG:BaseUrl"];
        var token = configuration["RAG:Token"];
        _ragClient = new RAGClient(baseUrl, token);
    }
    
    [HttpPost("ask")]
    public async Task<IActionResult> AskQuestion([FromBody] AskRequest request)
    {
        try
        {
            var result = await _ragClient.QueryAsync(request.Question, request.TenantId);
            
            return Ok(new
            {
                Success = true,
                Answer = result.Answer,
                Sources = result.Sources
            });
        }
        catch (Exception ex)
        {
            return StatusCode(500, new
            {
                Success = false,
                Error = ex.Message
            });
        }
    }
    
    [HttpPost("upload")]
    public async Task<IActionResult> UploadDocument(IFormFile file, [FromForm] string tenantId = "default")
    {
        try
        {
            if (file == null || file.Length == 0)
            {
                return BadRequest(new { Error = "No file provided" });
            }
            
            var tempPath = Path.GetTempFileName();
            using (var stream = new FileStream(tempPath, FileMode.Create))
            {
                await file.CopyToAsync(stream);
            }
            
            var result = await _ragClient.UploadDocumentAsync(tempPath, tenantId);
            
            System.IO.File.Delete(tempPath);
            
            return Ok(new
            {
                Success = true,
                Chunks = result.Chunks,
                Message = result.Message
            });
        }
        catch (Exception ex)
        {
            return StatusCode(500, new
            {
                Success = false,
                Error = ex.Message
            });
        }
    }
}

public class AskRequest
{
    public string Question { get; set; }
    public string TenantId { get; set; } = "default";
}
```

## PHP Integration

```php
<?php

class RAGClient
{
    private $baseUrl;
    private $token;
    
    public function __construct($baseUrl, $token)
    {
        $this->baseUrl = rtrim($baseUrl, '/');
        $this->token = $token;
    }
    
    public function query($question, $tenantId = 'default')
    {
        $url = $tenantId === 'default' 
            ? $this->baseUrl . '/query'
            : $this->baseUrl . '/query/tenant';
        
        $data = ['query' => $question];
        if ($tenantId !== 'default') {
            $data['tenant_id'] = $tenantId;
        }
        
        return $this->makeRequest('POST', $url, $data);
    }
    
    public function uploadDocument($filePath, $tenantId = 'default')
    {
        $url = $tenantId === 'default'
            ? $this->baseUrl . '/upload'
            : $this->baseUrl . '/upload/tenant?tenant_id=' . urlencode($tenantId);
        
        $postData = [
            'file' => new CURLFile($filePath)
        ];
        
        return $this->makeRequest('POST', $url, $postData, true);
    }
    
    private function makeRequest($method, $url, $data = null, $isMultipart = false)
    {
        $ch = curl_init();
        
        curl_setopt_array($ch, [
            CURLOPT_URL => $url,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_HTTPHEADER => [
                'Authorization: Bearer ' . $this->token,
                $isMultipart ? '' : 'Content-Type: application/json'
            ],
            CURLOPT_CUSTOMREQUEST => $method,
            CURLOPT_POSTFIELDS => $isMultipart ? $data : json_encode($data)
        ]);
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        
        if (curl_errno($ch)) {
            throw new Exception('cURL Error: ' . curl_error($ch));
        }
        
        curl_close($ch);
        
        if ($httpCode >= 400) {
            throw new Exception('HTTP Error: ' . $httpCode);
        }
        
        return json_decode($response, true);
    }
}

// Usage
$client = new RAGClient('http://localhost:8000', 'your_jwt_token');

try {
    $result = $client->query('What is the main topic?', 'company_example_com');
    echo "Answer: " . $result['answer'] . "\n";
    
    $uploadResult = $client->uploadDocument('document.pdf', 'company_example_com');
    echo "Uploaded " . $uploadResult['chunks'] . " chunks\n";
} catch (Exception $e) {
    echo "Error: " . $e->getMessage() . "\n";
}
?>
```

## Go Integration

```go
package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "io"
    "mime/multipart"
    "net/http"
    "os"
    "path/filepath"
)

type RAGClient struct {
    BaseURL string
    Token   string
    Client  *http.Client
}

func NewRAGClient(baseURL, token string) *RAGClient {
    return &RAGClient{
        BaseURL: baseURL,
        Token:   token,
        Client:  &http.Client{},
    }
}

func (c *RAGClient) Query(question, tenantID string) (map[string]interface{}, error) {
    url := c.BaseURL + "/query"
    if tenantID != "default" {
        url = c.BaseURL + "/query/tenant"
    }
    
    data := map[string]interface{}{
        "query": question,
    }
    if tenantID != "default" {
        data["tenant_id"] = tenantID
    }
    
    jsonData, err := json.Marshal(data)
    if err != nil {
        return nil, err
    }
    
    req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
    if err != nil {
        return nil, err
    }
    
    req.Header.Set("Authorization", "Bearer "+c.Token)
    req.Header.Set("Content-Type", "application/json")
    
    resp, err := c.Client.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    
    if resp.StatusCode >= 400 {
        return nil, fmt.Errorf("HTTP error: %d", resp.StatusCode)
    }
    
    var result map[string]interface{}
    err = json.NewDecoder(resp.Body).Decode(&result)
    return result, err
}

func (c *RAGClient) UploadDocument(filePath, tenantID string) (map[string]interface{}, error) {
    url := c.BaseURL + "/upload"
    if tenantID != "default" {
        url = c.BaseURL + "/upload/tenant?tenant_id=" + tenantID
    }
    
    file, err := os.Open(filePath)
    if err != nil {
        return nil, err
    }
    defer file.Close()
    
    var b bytes.Buffer
    w := multipart.NewWriter(&b)
    
    fw, err := w.CreateFormFile("file", filepath.Base(filePath))
    if err != nil {
        return nil, err
    }
    
    if _, err = io.Copy(fw, file); err != nil {
        return nil, err
    }
    w.Close()
    
    req, err := http.NewRequest("POST", url, &b)
    if err != nil {
        return nil, err
    }
    
    req.Header.Set("Authorization", "Bearer "+c.Token)
    req.Header.Set("Content-Type", w.FormDataContentType())
    
    resp, err := c.Client.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    
    if resp.StatusCode >= 400 {
        return nil, fmt.Errorf("HTTP error: %d", resp.StatusCode)
    }
    
    var result map[string]interface{}
    err = json.NewDecoder(resp.Body).Decode(&result)
    return result, err
}

func main() {
    client := NewRAGClient("http://localhost:8000", "your_jwt_token")
    
    // Query documents
    result, err := client.Query("What is the main topic?", "company_example_com")
    if err != nil {
        fmt.Printf("Error: %v\n", err)
        return
    }
    
    fmt.Printf("Answer: %v\n", result["answer"])
    
    // Upload document
    uploadResult, err := client.UploadDocument("document.pdf", "company_example_com")
    if err != nil {
        fmt.Printf("Upload error: %v\n", err)
        return
    }
    
    fmt.Printf("Uploaded %v chunks\n", uploadResult["chunks"])
}
```

## Ruby Integration

```ruby
require 'net/http'
require 'json'
require 'uri'

class RAGClient
  def initialize(base_url, token)
    @base_url = base_url.chomp('/')
    @token = token
  end
  
  def query(question, tenant_id = 'default')
    url = tenant_id == 'default' ? "#{@base_url}/query" : "#{@base_url}/query/tenant"
    
    data = { query: question }
    data[:tenant_id] = tenant_id unless tenant_id == 'default'
    
    make_request('POST', url, data)
  end
  
  def upload_document(file_path, tenant_id = 'default')
    url = tenant_id == 'default' ? "#{@base_url}/upload" : "#{@base_url}/upload/tenant?tenant_id=#{tenant_id}"
    
    uri = URI(url)
    request = Net::HTTP::Post.new(uri)
    request['Authorization'] = "Bearer #{@token}"
    
    form_data = [['file', File.open(file_path)]]
    request.set_form(form_data, 'multipart/form-data')
    
    response = Net::HTTP.start(uri.hostname, uri.port) do |http|
      http.request(request)
    end
    
    raise "HTTP Error: #{response.code}" if response.code.to_i >= 400
    
    JSON.parse(response.body)
  end
  
  private
  
  def make_request(method, url, data = nil)
    uri = URI(url)
    request = case method
              when 'POST'
                Net::HTTP::Post.new(uri)
              when 'GET'
                Net::HTTP::Get.new(uri)
              end
    
    request['Authorization'] = "Bearer #{@token}"
    request['Content-Type'] = 'application/json'
    request.body = data.to_json if data
    
    response = Net::HTTP.start(uri.hostname, uri.port) do |http|
      http.request(request)
    end
    
    raise "HTTP Error: #{response.code}" if response.code.to_i >= 400
    
    JSON.parse(response.body)
  end
end

# Usage
client = RAGClient.new('http://localhost:8000', 'your_jwt_token')

begin
  result = client.query('What is the main topic?', 'company_example_com')
  puts "Answer: #{result['answer']}"
  
  upload_result = client.upload_document('document.pdf', 'company_example_com')
  puts "Uploaded #{upload_result['chunks']} chunks"
rescue => e
  puts "Error: #{e.message}"
end
```

## Webhook Integration

### Setting up Webhooks

```python
# webhook_handler.py
from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

@app.route('/webhook/rag', methods=['POST'])
def handle_rag_webhook():
    """Handle incoming webhook from RAG system"""
    try:
        data = request.json
        
        # Process the webhook data
        event_type = data.get('event_type')
        tenant_id = data.get('tenant_id')
        
        if event_type == 'document_uploaded':
            # Handle document upload event
            document_info = data.get('document')
            print(f"Document uploaded: {document_info['filename']} for tenant {tenant_id}")
            
        elif event_type == 'query_processed':
            # Handle query processing event
            query_info = data.get('query')
            print(f"Query processed: {query_info['question']} for tenant {tenant_id}")
            
        elif event_type == 'tenant_created':
            # Handle tenant creation event
            tenant_info = data.get('tenant')
            print(f"New tenant created: {tenant_info['company_name']}")
            
        return jsonify({'status': 'success'})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000)
```

### Sending Webhooks from RAG System

```python
# Add to your RAG system
import requests
import json

def send_webhook(webhook_url, event_type, data):
    """Send webhook notification"""
    payload = {
        'event_type': event_type,
        'timestamp': datetime.utcnow().isoformat(),
        **data
    }
    
    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Webhook failed: {e}")

# Usage in your RAG endpoints
@app.post("/upload")
async def upload_doc(file: UploadFile = File(...), tenant_id: str = Query("default")):
    # ... existing upload logic ...
    
    # Send webhook
    send_webhook(
        "http://your-app.com/webhook/rag",
        "document_uploaded",
        {
            "tenant_id": tenant_id,
            "document": {
                "filename": file.filename,
                "chunks": result["chunks"]
            }
        }
    )
    
    return result
```

## Best Practices

### 1. Error Handling
```python
try:
    result = client.query("What is AI?", "company_example_com")
    print(result['answer'])
except RAGError as e:
    print(f"RAG Error: {e}")
except requests.exceptions.RequestException as e:
    print(f"Network Error: {e}")
except Exception as e:
    print(f"Unexpected Error: {e}")
```

### 2. Retry Logic
```python
import time
from functools import wraps

def retry(max_attempts=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise e
                    time.sleep(delay * (2 ** attempt))
            return None
        return wrapper
    return decorator

@retry(max_attempts=3, delay=1)
def query_with_retry(client, question, tenant_id):
    return client.query(question, tenant_id)
```

### 3. Rate Limiting
```python
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_requests=100, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = defaultdict(list)
    
    def is_allowed(self, key):
        now = time.time()
        # Remove old requests
        self.requests[key] = [req_time for req_time in self.requests[key] 
                            if now - req_time < self.time_window]
        
        if len(self.requests[key]) >= self.max_requests:
            return False
        
        self.requests[key].append(now)
        return True

# Usage
rate_limiter = RateLimiter(max_requests=100, time_window=60)

def query_with_rate_limit(client, question, tenant_id):
    if not rate_limiter.is_allowed(tenant_id):
        raise Exception("Rate limit exceeded")
    
    return client.query(question, tenant_id)
```

### 4. Caching
```python
from functools import lru_cache
import hashlib

class CachedRAGClient(RAGClient):
    @lru_cache(maxsize=1000)
    def query(self, question, tenant_id="default"):
        # Create cache key
        cache_key = hashlib.md5(f"{question}:{tenant_id}".encode()).hexdigest()
        
        # Check cache first
        cached_result = self.get_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        # Make API call
        result = super().query(question, tenant_id)
        
        # Cache result
        self.set_cache(cache_key, result)
        
        return result
```

### 5. Monitoring and Logging
```python
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MonitoredRAGClient(RAGClient):
    def query(self, question, tenant_id="default"):
        start_time = time.time()
        
        try:
            result = super().query(question, tenant_id)
            
            duration = time.time() - start_time
            logger.info(f"Query successful: {question[:50]}... (tenant: {tenant_id}, duration: {duration:.2f}s)")
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Query failed: {question[:50]}... (tenant: {tenant_id}, duration: {duration:.2f}s, error: {e})")
            raise
```

This comprehensive integration guide provides everything you need to integrate the Multi-Tenant RAG system into your applications using various programming languages and frameworks. Each example includes error handling, best practices, and real-world usage patterns.

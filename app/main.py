from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn, os
from app.rag_advanced import process_query, process_document_upload, advanced_rag
from app.rag_multi_tenant import multi_tenant_rag_engine
from app.tenant_api import router as tenant_router
from app.multi_tenant import multi_tenant_rag
from app.auth import verify_token

class QueryRequest(BaseModel):
    query: str
    tenant_id: str = "default"  # Default tenant for backward compatibility

class TenantQueryRequest(BaseModel):
    query: str
    tenant_id: str

app = FastAPI(title="Multi-Tenant RAG Chatbot API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Include tenant management routes
app.include_router(tenant_router)

# Serve web interface
@app.get("/")
async def root():
    """Serve the main web interface"""
    return FileResponse("web_interface.html")

@app.get("/web_interface")
async def web_interface():
    """Serve the web interface"""
    return FileResponse("web_interface.html")

@app.get("/web_interface.html")
async def web_interface_html():
    """Serve the web interface HTML file"""
    return FileResponse("web_interface.html")

@app.post("/query")
async def ask_question(request: QueryRequest, token: HTTPAuthorizationCredentials = Depends(security)):
    verify_token(token) # raises 401 on invalid
    
    # Use multi-tenant engine if tenant_id is provided and not default
    if request.tenant_id != "default":
        response = await multi_tenant_rag_engine.process_query(request.tenant_id, request.query)
    else:
        # Fallback to single-tenant engine for backward compatibility
        response = await process_query(request.query)
    
    return response

@app.post("/query/tenant")
async def ask_question_tenant(request: TenantQueryRequest, token: HTTPAuthorizationCredentials = Depends(security)):
    """Tenant-specific query endpoint"""
    verify_token(token)
    response = await multi_tenant_rag_engine.process_query(request.tenant_id, request.query)
    return response

@app.post("/upload")
async def upload_doc(
    file: UploadFile = File(...), 
    tenant_id: str = Query("default"),
    token: HTTPAuthorizationCredentials = Depends(security)
):
    verify_token(token)
    
    # Use multi-tenant engine if tenant_id is provided and not default
    if tenant_id != "default":
        result = multi_tenant_rag_engine.process_document_upload(tenant_id, file)
        return result
    else:
        # Fallback to single-tenant engine for backward compatibility
        chunks = process_document_upload(file)
        return {"chunks": chunks, "status": "indexed"}

@app.post("/upload/tenant")
async def upload_doc_tenant(
    file: UploadFile = File(...),
    tenant_id: str = Query(...),
    token: HTTPAuthorizationCredentials = Depends(security)
):
    """Tenant-specific upload endpoint"""
    verify_token(token)
    result = multi_tenant_rag_engine.process_document_upload(tenant_id, file)
    return result

@app.get("/healthcheck")
def healthcheck():
    return {"status": "ok"}

@app.get("/get-token")
def get_token():
    """Generate a JWT token for web interface testing"""
    from app.auth import SECRET_KEY
    from jose import jwt
    import time
    
    payload = {
        "user_id": "web_interface_user",
        "exp": int(time.time()) + 3600  # 1 hour expiry
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return {"token": token}

@app.get("/collection-info")
def get_collection_info(
    tenant_id: str = Query("default"),
    token: HTTPAuthorizationCredentials = Depends(security)
):
    """Get information about the current document collection"""
    verify_token(token)
    
    if tenant_id != "default":
        return multi_tenant_rag_engine.get_tenant_collection_info(tenant_id)
    else:
        return advanced_rag.get_collection_info()

@app.get("/document-count")
def get_document_count(
    tenant_id: str = Query("default"),
    token: HTTPAuthorizationCredentials = Depends(security)
):
    """Get the number of documents in the collection"""
    verify_token(token)
    
    if tenant_id != "default":
        count = multi_tenant_rag_engine.get_tenant_document_count(tenant_id)
        return {"document_count": count, "tenant_id": tenant_id}
    else:
        return {"document_count": advanced_rag.get_document_count()}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

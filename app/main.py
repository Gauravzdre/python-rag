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
from app.auth import verify_token, verify_auth

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
    auth_info = verify_auth(token)
    
    # If using tenant API key, verify the tenant_id matches
    if auth_info.get("auth_type") == "tenant_api_key":
        if auth_info.get("tenant_id") != request.tenant_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant ID mismatch")
    
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
    auth_info = verify_auth(token)
    
    # If using tenant API key, verify the tenant_id matches
    if auth_info.get("auth_type") == "tenant_api_key":
        if auth_info.get("tenant_id") != tenant_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant ID mismatch")
    
    result = multi_tenant_rag_engine.process_document_upload(tenant_id, file)
    return result

@app.get("/healthcheck")
def healthcheck():
    return {"status": "ok"}

@app.get("/debug/tenants")
def debug_tenants(token: HTTPAuthorizationCredentials = Depends(security)):
    """Debug endpoint to check tenant data"""
    verify_token(token)
    
    try:
        # Check which database manager is being used
        try:
            from app.postgres_database import postgres_manager
            db_type = "SQLAlchemy PostgreSQL"
        except Exception:
            from app.simple_postgres import simple_postgres_manager as postgres_manager
            db_type = "Simple PostgreSQL"
        
        # Get all tenants
        tenants = multi_tenant_rag.list_tenants()
        
        # Check for specific tenant with different possible IDs
        omegagaze_tenant = multi_tenant_rag.get_tenant("omegagaze_com")
        omegagaze_tenant2 = multi_tenant_rag.get_tenant("omegagaze")
        omegagaze_tenant3 = multi_tenant_rag.get_tenant("omegagaze_online")
        
        return {
            "database_type": db_type,
            "total_tenants": len(tenants),
            "tenants": tenants,
            "omegagaze_com_exists": omegagaze_tenant is not None,
            "omegagaze_exists": omegagaze_tenant2 is not None,
            "omegagaze_online_exists": omegagaze_tenant3 is not None,
            "omegagaze_com_data": omegagaze_tenant,
            "omegagaze_data": omegagaze_tenant2,
            "omegagaze_online_data": omegagaze_tenant3
        }
    except Exception as e:
        return {"error": str(e)}

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

# Tenant-specific endpoints (no admin access required)

@app.get("/tenants/{tenant_id}/documents")
async def get_tenant_documents(
    tenant_id: str,
    token: HTTPAuthorizationCredentials = Depends(security)
):
    """Get all documents for a tenant"""
    auth_info = verify_auth(token)
    
    # If using tenant API key, verify the tenant_id matches
    if auth_info.get("auth_type") == "tenant_api_key":
        if auth_info.get("tenant_id") != tenant_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant ID mismatch")
    
    documents = multi_tenant_rag.get_tenant_documents(tenant_id)
    
    return {
        "tenant_id": tenant_id,
        "documents": documents,
        "total_count": len(documents)
    }

@app.get("/collection-info")
async def get_collection_info(
    tenant_id: str = Query("default"),
    token: HTTPAuthorizationCredentials = Depends(security)
):
    """Get information about the current document collection"""
    auth_info = verify_auth(token)
    
    # If using tenant API key, verify the tenant_id matches
    if auth_info.get("auth_type") == "tenant_api_key":
        if auth_info.get("tenant_id") != tenant_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant ID mismatch")
    
    if tenant_id != "default":
        # Get tenant info
        tenant = multi_tenant_rag.get_tenant(tenant_id)
        if not tenant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        
        # Get documents count
        documents = multi_tenant_rag.get_tenant_documents(tenant_id)
        
        return {
            "tenant_id": tenant_id,
            "company_name": tenant.get("company_name"),
            "document_count": len(documents),
            "max_documents": tenant.get("max_documents", 100),
            "plan": tenant.get("plan", "basic")
        }
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

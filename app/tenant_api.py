"""
Multi-Tenant API endpoints
Handles tenant registration, management, and operations
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Dict, List, Optional
import logging

from app.multi_tenant import multi_tenant_rag
from app.auth import verify_token

logger = logging.getLogger(__name__)

# Create router for tenant endpoints
router = APIRouter(prefix="/tenants", tags=["Multi-Tenant Management"])
security = HTTPBearer()

# Pydantic models for tenant operations
class TenantRegistration(BaseModel):
    company_name: str
    company_domain: str
    company_email: EmailStr
    company_phone: Optional[str] = None
    plan: str = "basic"
    max_documents: int = 100
    max_queries_per_day: int = 1000
    ai_personality: str = "helpful"
    response_style: str = "concise"
    primary_color: str = "#007bff"
    company_description: Optional[str] = None

class TenantUpdate(BaseModel):
    company_name: Optional[str] = None
    company_domain: Optional[str] = None
    company_email: Optional[EmailStr] = None
    company_phone: Optional[str] = None
    plan: Optional[str] = None
    max_documents: Optional[int] = None
    max_queries_per_day: Optional[int] = None
    ai_personality: Optional[str] = None
    response_style: Optional[str] = None
    primary_color: Optional[str] = None
    company_description: Optional[str] = None
    status: Optional[str] = None

class TenantResponse(BaseModel):
    tenant_id: str
    company_name: str
    company_domain: str
    company_email: str
    api_key: str
    status: str
    plan: str
    created_at: str
    document_count: int
    total_queries: int

class TenantListResponse(BaseModel):
    tenants: List[Dict]
    total_count: int

class TenantStatsResponse(BaseModel):
    tenant_info: Dict
    total_documents: int
    total_queries: int
    queries_today: int
    popular_queries: List[str]
    document_types: Dict

# Helper function to verify admin access
def verify_admin_access(token: HTTPAuthorizationCredentials = Depends(security)):
    """Verify that the user has admin access for tenant management"""
    # For now, we'll use a simple check - in production, you'd check user roles
    payload = verify_token(token)
    # Add role checking logic here
    return payload

@router.post("/register", response_model=TenantResponse)
async def register_tenant(
    tenant_data: TenantRegistration,
    admin_token: HTTPAuthorizationCredentials = Depends(verify_admin_access)
):
    """Register a new tenant (company)"""
    try:
        # Generate tenant ID from company domain
        tenant_id = tenant_data.company_domain.replace(".", "_").replace("-", "_").lower()
        
        # Check if tenant already exists
        if multi_tenant_rag.get_tenant(tenant_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tenant with domain {tenant_data.company_domain} already exists"
            )
        
        # Add tenant
        success = multi_tenant_rag.add_tenant(tenant_id, tenant_data.dict())
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create tenant"
            )
        
        # Get created tenant info
        tenant_info = multi_tenant_rag.get_tenant(tenant_id)
        tenant_docs = multi_tenant_rag.get_tenant_documents(tenant_id)
        tenant_stats = multi_tenant_rag.get_tenant_stats(tenant_id)
        
        return TenantResponse(
            tenant_id=tenant_id,
            company_name=tenant_info["company_name"],
            company_domain=tenant_info["company_domain"],
            company_email=tenant_info["company_email"],
            api_key=tenant_info["api_key"],
            status=tenant_info["status"],
            plan=tenant_info["plan"],
            created_at=tenant_info["created_at"],
            document_count=len(tenant_docs),
            total_queries=tenant_stats.get("total_queries", 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering tenant: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/", response_model=TenantListResponse)
async def list_tenants(
    admin_token: HTTPAuthorizationCredentials = Depends(verify_admin_access)
):
    """List all tenants"""
    try:
        tenants = multi_tenant_rag.list_tenants()
        return TenantListResponse(
            tenants=tenants,
            total_count=len(tenants)
        )
    except Exception as e:
        logger.error(f"Error listing tenants: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    admin_token: HTTPAuthorizationCredentials = Depends(verify_admin_access)
):
    """Get specific tenant information"""
    try:
        tenant_info = multi_tenant_rag.get_tenant(tenant_id)
        
        if not tenant_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {tenant_id} not found"
            )
        
        tenant_docs = multi_tenant_rag.get_tenant_documents(tenant_id)
        tenant_stats = multi_tenant_rag.get_tenant_stats(tenant_id)
        
        return TenantResponse(
            tenant_id=tenant_id,
            company_name=tenant_info["company_name"],
            company_domain=tenant_info["company_domain"],
            company_email=tenant_info["company_email"],
            api_key=tenant_info["api_key"],
            status=tenant_info["status"],
            plan=tenant_info["plan"],
            created_at=tenant_info["created_at"],
            document_count=len(tenant_docs),
            total_queries=tenant_stats.get("total_queries", 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tenant {tenant_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.put("/{tenant_id}")
async def update_tenant(
    tenant_id: str,
    updates: TenantUpdate,
    admin_token: HTTPAuthorizationCredentials = Depends(verify_admin_access)
):
    """Update tenant configuration"""
    try:
        # Check if tenant exists
        if not multi_tenant_rag.get_tenant(tenant_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {tenant_id} not found"
            )
        
        # Filter out None values
        update_data = {k: v for k, v in updates.dict().items() if v is not None}
        
        success = multi_tenant_rag.update_tenant(tenant_id, update_data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update tenant"
            )
        
        return {"message": f"Tenant {tenant_id} updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tenant {tenant_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.delete("/{tenant_id}")
async def delete_tenant(
    tenant_id: str,
    admin_token: HTTPAuthorizationCredentials = Depends(verify_admin_access)
):
    """Delete a tenant and all associated data"""
    try:
        # Check if tenant exists
        if not multi_tenant_rag.get_tenant(tenant_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {tenant_id} not found"
            )
        
        success = multi_tenant_rag.delete_tenant(tenant_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete tenant"
            )
        
        return {"message": f"Tenant {tenant_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting tenant {tenant_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/{tenant_id}/stats", response_model=TenantStatsResponse)
async def get_tenant_stats(
    tenant_id: str,
    admin_token: HTTPAuthorizationCredentials = Depends(verify_admin_access)
):
    """Get comprehensive statistics for a tenant"""
    try:
        # Check if tenant exists
        if not multi_tenant_rag.get_tenant(tenant_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {tenant_id} not found"
            )
        
        stats = multi_tenant_rag.get_tenant_stats(tenant_id)
        
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No statistics found for tenant {tenant_id}"
            )
        
        return TenantStatsResponse(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stats for tenant {tenant_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/{tenant_id}/documents")
async def get_tenant_documents(
    tenant_id: str,
    admin_token: HTTPAuthorizationCredentials = Depends(verify_admin_access)
):
    """Get all documents for a tenant"""
    try:
        # Check if tenant exists
        if not multi_tenant_rag.get_tenant(tenant_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {tenant_id} not found"
            )
        
        documents = multi_tenant_rag.get_tenant_documents(tenant_id)
        
        return {
            "tenant_id": tenant_id,
            "documents": documents,
            "total_count": len(documents)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting documents for tenant {tenant_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.delete("/{tenant_id}/documents/{document_id}")
async def delete_tenant_document(
    tenant_id: str,
    document_id: str,
    admin_token: HTTPAuthorizationCredentials = Depends(verify_admin_access)
):
    """Delete a specific document from a tenant"""
    try:
        # Check if tenant exists
        if not multi_tenant_rag.get_tenant(tenant_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {tenant_id} not found"
            )
        
        success = multi_tenant_rag.delete_document(tenant_id, document_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found for tenant {tenant_id}"
            )
        
        return {"message": f"Document {document_id} deleted successfully from tenant {tenant_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id} from tenant {tenant_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

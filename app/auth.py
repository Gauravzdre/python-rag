import os
from fastapi import HTTPException, status
from jose import jwt, JWTError
from typing import Optional, Dict

SECRET_KEY = os.getenv("JWT_SECRET", "supersecret")
ALGORITHM = "HS256"

def verify_token(credentials):
    """Verify JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth")

def verify_tenant_api_key(credentials) -> Optional[Dict]:
    """Verify tenant API key and return tenant info"""
    try:
        from app.postgres_database import postgres_manager
        
        # Extract API key from Bearer token
        api_key = credentials.credentials
        
        # Check if it's a tenant API key (starts with 'mt_')
        if api_key.startswith('mt_'):
            tenant = postgres_manager.get_tenant_by_api_key(api_key)
            if tenant:
                return {
                    "tenant_id": tenant["tenant_id"],
                    "company_name": tenant["company_name"],
                    "api_key": api_key,
                    "auth_type": "tenant_api_key"
                }
        
        return None
    except Exception as e:
        return None

def verify_auth(credentials):
    """Verify either JWT token or tenant API key"""
    # First try JWT token
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        payload["auth_type"] = "jwt"
        return payload
    except JWTError:
        pass
    
    # If JWT fails, try tenant API key
    tenant_info = verify_tenant_api_key(credentials)
    if tenant_info:
        return tenant_info
    
    # If both fail, raise unauthorized
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth")

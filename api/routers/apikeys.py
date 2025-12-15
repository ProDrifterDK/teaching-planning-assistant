from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..db.session import get_db
from ..db.models import User
from ..db.apikey_crud import (
    create_service_client,
    deactivate_client,
    rotate_api_key,
    list_service_clients
)
from ..routers.auth import get_current_admin_user

router = APIRouter(prefix="/admin/apikeys", tags=["API Keys"])

class CreateAPIKeyRequest(BaseModel):
    client_name: str
    permissions: List[str] = ["*"]  # Default all permissions
    rate_limit: int = 100
    webhook_url: Optional[str] = None

class APIKeyResponse(BaseModel):
    id: int
    client_name: str
    permissions: List[str]
    rate_limit: int
    is_active: bool
    created_at: datetime
    last_used: Optional[datetime]
    webhook_url: Optional[str]

    class Config:
        from_attributes = True

class CreateAPIKeyResponse(APIKeyResponse):
    api_key: str  # Only returned on creation!

@router.post("/", response_model=CreateAPIKeyResponse)
def create_api_key(
    request: CreateAPIKeyRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new API key (Admin only). The API key is only shown once!"""
    try:
        client, raw_api_key = create_service_client(
            db,
            client_name=request.client_name,
            permissions=request.permissions,
            rate_limit=request.rate_limit,
            webhook_url=request.webhook_url
        )
        
        # Convert SQLAlchemy model to Pydantic model manually to include api_key
        response = CreateAPIKeyResponse(
            id=client.id,
            client_name=client.client_name,
            permissions=client.permissions,
            rate_limit=client.rate_limit,
            is_active=client.is_active,
            created_at=client.created_at,
            last_used=client.last_used,
            webhook_url=client.webhook_url,
            api_key=raw_api_key
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[APIKeyResponse])
def list_api_keys(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List all API keys (Admin only)"""
    return list_service_clients(db)

@router.delete("/{client_id}")
def deactivate_api_key(
    client_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Deactivate an API key (Admin only)"""
    if not deactivate_client(db, client_id):
        raise HTTPException(status_code=404, detail="Client not found")
    return {"message": "API key deactivated successfully"}

@router.post("/{client_id}/rotate", response_model=CreateAPIKeyResponse)
def rotate_client_api_key(
    client_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Rotate (regenerate) an API key (Admin only)"""
    client, raw_api_key = rotate_api_key(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
        
    response = CreateAPIKeyResponse(
        id=client.id,
        client_name=client.client_name,
        permissions=client.permissions,
        rate_limit=client.rate_limit,
        is_active=client.is_active,
        created_at=client.created_at,
        last_used=client.last_used,
        webhook_url=client.webhook_url,
        api_key=raw_api_key
    )
    return response
from sqlalchemy.orm import Session
from sqlalchemy import select
from passlib.hash import sha256_crypt
import secrets
from datetime import datetime
from typing import Optional, Tuple, List

from .models import ServiceClient

def generate_api_key() -> str:
    """Generate a secure API key with tpa_ prefix"""
    return f"tpa_{secrets.token_urlsafe(32)}"

def hash_api_key(api_key: str) -> str:
    """Hash API key for storage"""
    return sha256_crypt.hash(api_key)

def verify_api_key(api_key: str, hash: str) -> bool:
    """Verify API key against stored hash"""
    return sha256_crypt.verify(api_key, hash)

def get_client_by_api_key(db: Session, api_key: str) -> Optional[ServiceClient]:
    """Find and verify a client by API key"""
    # Query all active clients
    # Note: Since we can't query by hash directly (salt), we need to check candidates
    # In a production system with many keys, we might want to store a key prefix for faster lookup
    # For now, we'll iterate active clients. If this scales up, we'll add a key_prefix column.
    
    active_clients = db.query(ServiceClient).filter(ServiceClient.is_active == True).all()
    
    for client in active_clients:
        if verify_api_key(api_key, client.api_key_hash):
            return client
            
    return None

def create_service_client(
    db: Session, 
    client_name: str, 
    permissions: list, 
    rate_limit: int = 100, 
    webhook_url: Optional[str] = None
) -> Tuple[ServiceClient, str]:
    """Create a new service client and return (client, raw_api_key)"""
    raw_api_key = generate_api_key()
    api_key_hash = hash_api_key(raw_api_key)
    
    db_client = ServiceClient(
        client_name=client_name,
        api_key_hash=api_key_hash,
        permissions=permissions,
        rate_limit=rate_limit,
        webhook_url=webhook_url
    )
    
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    
    return db_client, raw_api_key

def update_client_last_used(db: Session, client_id: int) -> None:
    """Update the last_used timestamp"""
    client = db.query(ServiceClient).filter(ServiceClient.id == client_id).first()
    if client:
        client.last_used = datetime.utcnow()
        db.commit()

def deactivate_client(db: Session, client_id: int) -> bool:
    """Deactivate a service client"""
    client = db.query(ServiceClient).filter(ServiceClient.id == client_id).first()
    if client:
        client.is_active = False
        db.commit()
        return True
    return False

def rotate_api_key(db: Session, client_id: int) -> Tuple[Optional[ServiceClient], Optional[str]]:
    """Rotate API key for a client"""
    client = db.query(ServiceClient).filter(ServiceClient.id == client_id).first()
    if not client:
        return None, None
        
    raw_api_key = generate_api_key()
    client.api_key_hash = hash_api_key(raw_api_key)
    db.commit()
    db.refresh(client)
    
    return client, raw_api_key

def list_service_clients(db: Session) -> List[ServiceClient]:
    """List all service clients (without exposing keys)"""
    return db.query(ServiceClient).all()
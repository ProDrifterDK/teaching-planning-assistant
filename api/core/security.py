from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Security, Depends, HTTPException
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .config import settings
from ..db.session import get_db
from ..db.models import ServiceClient, User
from ..db.apikey_crud import get_client_by_api_key, update_client_last_used

# Configuración para el hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña en texto plano contra su hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Genera el hash de una contraseña."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un nuevo token de acceso JWT.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Por defecto, los tokens expirarán en 15 minutos
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str, credentials_exception) -> str:
    """
    Verifica un token JWT y devuelve el nombre de usuario (sub).
    Lanza credentials_exception si el token es inválido.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception

# API Key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_api_key_client(
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db)
) -> ServiceClient:
    """
    Validate API key and return the ServiceClient.
    Raises HTTPException 401 if invalid.
    """
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key is required",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    client = get_client_by_api_key(db, api_key)
    if not client:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    if not client.is_active:
        raise HTTPException(
            status_code=403,
            detail="API key has been deactivated"
        )
    
    # Update last_used timestamp
    update_client_last_used(db, client.id)
    
    return client

def require_permission(permission: str):
    """
    Dependency factory to check if client has specific permission.
    Usage: Depends(require_permission("content:generate"))
    """
    def check_permission(client: ServiceClient = Depends(get_api_key_client)):
        if permission not in client.permissions and "*" not in client.permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Missing required permission: {permission}"
            )
        return client
    return check_permission

# Combined auth - accepts either JWT or API Key
def get_current_user_or_client(
    token: Optional[str] = Depends(oauth2_scheme),
    api_key: Optional[str] = Security(api_key_header),
    db: Session = Depends(get_db)
) -> Union[User, ServiceClient]:
    """
    Accepts either JWT token OR API key for authentication.
    Returns User for JWT, ServiceClient for API key.
    """
    if api_key:
        return get_api_key_client(api_key, db)
    
    if token:
        from ..db.user_crud import get_user_by_username
        credentials_exception = HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        username = verify_token(token, credentials_exception)
        user = get_user_by_username(db, username=username)
        if user is None:
            raise credentials_exception
        return user
        
    raise HTTPException(
        status_code=401,
        detail="Authentication required (JWT or API Key)",
        headers={"WWW-Authenticate": "Bearer, ApiKey"}
    )
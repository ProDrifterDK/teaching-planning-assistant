from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
import logging
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..core import security
from ..core.config import settings
from ..models import Token, User, UserCreate, UserUpdate, UserRoleUpdate
from ..services.user_service import UserService
from ..db.session import get_db

router = APIRouter(prefix="/auth", tags=["Authentication & Users"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

user_service = UserService()

# --- Dependency Functions ---

def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    username = security.verify_token(token, credentials_exception)
    if username is None:
        raise credentials_exception
    user = user_service.get_user(db, username=username)
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_active:
        logging.warning(
            f"Acceso denegado para usuario inactivo: '{current_user.username}'"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario está inactivo. Se requiere activación por parte de un administrador.",
        )
    return current_user

def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user
    
# --- Endpoints ---

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):
    user = user_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/users/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_create: UserCreate,
    db: Session = Depends(get_db),
):
    db_user = user_service.get_user(db=db, username=user_create.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    db_user_email = user_service.get_user_by_email(db=db, email=user_create.email)
    if db_user_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = user_service.create_user(db=db, user_create=user_create)
    return new_user

@router.get("/users/me", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Devuelve los datos del usuario actualmente autenticado, incluyendo su rol.
    """
    return current_user

@router.put("/users/{username}/status", response_model=User)
async def update_user_status(
    username: str,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    user_to_update = user_service.update_user_status(db, username, user_update.is_active)
    if not user_to_update:
        raise HTTPException(status_code=404, detail="User not found")
    return user_to_update

@router.put("/users/{username}/role", response_model=User)
async def update_user_role(
    username: str,
    user_role_update: UserRoleUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
):
    # Validar que el rol sea uno de los permitidos si es necesario
    allowed_roles = {"user", "admin"}
    if user_role_update.role not in allowed_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Allowed roles are: {', '.join(allowed_roles)}")

    user_to_update = user_service.update_user_role(db, username, user_role_update.role)
    if not user_to_update:
        raise HTTPException(status_code=404, detail="User not found")
    return user_to_update
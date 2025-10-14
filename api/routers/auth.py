from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from ..core import security
from ..core.config import settings
from ..models import Token, User, UserCreate, UserUpdate
from ..services.user_service import UserService, get_user_service

router = APIRouter(prefix="/auth", tags=["Authentication & Users"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# --- Dependency Functions ---

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_service: UserService = Depends(get_user_service),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    username = security.verify_token(token, credentials_exception)
    user = user_service.get_user(username=username)
    if user is None:
        raise credentials_exception
    return User(**user.dict())

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_admin_user(
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
    user_service: UserService = Depends(get_user_service),
):
    user = user_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password, or inactive user",
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
    user_service: UserService = Depends(get_user_service),
):
    db_user = user_service.get_user(username=user_create.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    new_user = user_service.create_user(user_create)
    return new_user

@router.get("/users/me", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user

@router.put("/users/{username}/status", response_model=User)
async def update_user_status(
    username: str,
    user_update: UserUpdate,
    admin_user: User = Depends(get_current_admin_user),
    user_service: UserService = Depends(get_user_service),
):
    user_to_update = user_service.update_user_status(username, user_update.is_active)
    if not user_to_update:
        raise HTTPException(status_code=404, detail="User not found")
    return user_to_update
from typing import Dict, Optional
from ..core import security
from ..models import UserInDB, UserCreate

# En una aplicación real, esto provendría de una base de datos.
# Contraseñas: admin -> 'adminpass', johndoe -> 'secret'
_fake_users_db: Dict[str, UserInDB] = {
    "admin": UserInDB(
        username="admin",
        full_name="Admin User",
        email="admin@example.com",
        hashed_password=security.get_password_hash("adminpass"),
        is_active=True,
        role="admin",
    ),
    "johndoe": UserInDB(
        username="johndoe",
        full_name="John Doe",
        email="johndoe@example.com",
        hashed_password=security.get_password_hash("secret"),
        is_active=False, # Por defecto inactivo hasta que un admin lo apruebe
        role="user",
    ),
}

class UserService:
    def get_user(self, username: str) -> Optional[UserInDB]:
        return _fake_users_db.get(username)

    def authenticate_user(self, username: str, password: str) -> Optional[UserInDB]:
        user = self.get_user(username)
        if not user or not security.verify_password(password, user.hashed_password):
            return None
        # Solo permite la autenticación si el usuario está activo
        if not user.is_active:
            return None
        return user

    def create_user(self, user_create: UserCreate) -> Optional[UserInDB]:
        if self.get_user(user_create.username):
            return None  # El usuario ya existe
        
        hashed_password = security.get_password_hash(user_create.password)
        
        new_user = UserInDB(
            username=user_create.username,
            full_name=user_create.full_name,
            email=user_create.email,
            hashed_password=hashed_password,
            is_active=False,  # Los nuevos usuarios se crean como inactivos
            role="user"
        )
        _fake_users_db[new_user.username] = new_user
        return new_user

    def update_user_status(self, username: str, is_active: bool) -> Optional[UserInDB]:
        user = self.get_user(username)
        if not user:
            return None
        
        user.is_active = is_active
        _fake_users_db[username] = user
        return user

# "Proveedor" de dependencias
_user_service_instance = UserService()

def get_user_service() -> UserService:
    return _user_service_instance
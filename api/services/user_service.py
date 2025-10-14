from typing import Dict, Optional
from ..core import security
from ..models import UserInDB

# --- "Data Base" en Memoria ---
# En una aplicación real, esto sería reemplazado por una base de datos.
# La contraseña para 'johndoe' es 'secret'.
fake_users_db: Dict[str, UserInDB] = {
    "johndoe": UserInDB(
        username="johndoe",
        full_name="John Doe",
        email="johndoe@example.com",
        hashed_password=security.get_password_hash("secret"),
        disabled=False,
    )
}

class UserService:
    def get_user(self, username: str) -> Optional[UserInDB]:
        """
        Busca un usuario en la base de datos.
        """
        return fake_users_db.get(username)

    def authenticate_user(self, username: str, password: str) -> Optional[UserInDB]:
        """
        Autentica a un usuario. Devuelve el usuario si las credenciales son válidas,
        de lo contrario devuelve None.
        """
        user = self.get_user(username)
        if not user:
            return None
        if not security.verify_password(password, user.hashed_password):
            return None
        return user

# "Proveedor" de dependencias para el servicio de usuario
_user_service_instance = UserService()

def get_user_service() -> UserService:
    return _user_service_instance
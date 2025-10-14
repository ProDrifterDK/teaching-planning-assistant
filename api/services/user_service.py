from sqlalchemy.orm import Session
from ..core import security
from ..models import UserCreate
from ..db import user_crud, models

class UserService:
    def get_user(self, db: Session, username: str):
        return user_crud.get_user_by_username(db, username)

    def get_user_by_email(self, db: Session, email: str):
        return user_crud.get_user_by_email(db, email)

    def authenticate_user(self, db: Session, username: str, password: str):
        user = self.get_user(db, username=username)
        if not user or not security.verify_password(password, user.hashed_password):
            return None
        return user

    def create_user(self, db: Session, user_create: UserCreate):
        return user_crud.create_user(db=db, user=user_create)

    def update_user_status(self, db: Session, username: str, is_active: bool):
        user = self.get_user(db, username=username)
        if not user:
            return None
        return user_crud.update_user_status(db=db, user=user, is_active=is_active)
    
    def update_user_role(self, db: Session, username: str, role: str):
        user = self.get_user(db, username=username)
        if not user:
            return None
        return user_crud.update_user_role(db=db, user=user, role=role)
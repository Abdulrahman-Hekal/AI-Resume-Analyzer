from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models import User
from app.core.security import get_password_hash

class UserRepository:
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email.lower().strip()).first()

    @staticmethod
    def create(db: Session, email: str, password: str, full_name: str, role: str = "user") -> User:
        user = User(
            email=email.lower().strip(),
            hashed_password=get_password_hash(password),
            full_name=full_name.strip(),
            role=role,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

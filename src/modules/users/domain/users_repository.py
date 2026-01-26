# src/modules/users/users_repository.py

from typing import List, Optional

from sqlmodel import Session, select

from src.shared.models.user.user_model import User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def admin_exists(self) -> bool:
        statement = (
            select(User.id)
            .where(
                User.is_admin.is_(True),
                User.is_active.is_(True),
            )
            .limit(1)
        )
        return self.session.exec(statement).first() is not None

    def get(self, user_id: int) -> Optional[User]:
        return self.session.get(User, user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        statement = select(User).where(User.email == email)
        return self.session.exec(statement).first()

    def list(self, skip: int = 0, limit: int = 100) -> List[User]:
        statement = select(User).offset(skip).limit(limit)
        return self.session.exec(statement).all()

    def add(self, user: User) -> User:
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def update(self, user: User) -> User:
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def delete(self, user: User) -> None:
        self.session.delete(user)
        self.session.commit()

import logging
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.db.models import User
from app.schemas.user import UserCreate, UserUpdate

logger = logging.getLogger(__name__)


def get_users(db: Session, skip: int = 0, limit: int = 100) -> Tuple[List[User], int]:
    """
    Получить список пользователей с пагинацией.
    """
    try:
        query = db.query(User)
        total = query.count()
        items = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
        return items, total
    except SQLAlchemyError as e:
        logger.error(f"Error fetching users: {e}")
        return [], 0

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """
    Получить пользователя по ID.
    """
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_telegram_id(db: Session, telegram_id: str) -> Optional[User]:
    """
    Получить пользователя по telegram_id.
    """
    return db.query(User).filter(User.telegram_id == telegram_id).first()

def create_user(db: Session, user_in: UserCreate) -> Optional[User]:
    """
    Создать нового пользователя.
    """
    if get_user_by_telegram_id(db, user_in.telegram_id):
        logger.error(f"User with telegram_id {user_in.telegram_id} already exists")
        return None
    try:
        db_user = User(
            telegram_id=user_in.telegram_id,
            username=user_in.username,
            email=user_in.email,
            whitelist_status=user_in.whitelist_status,
            settings=user_in.settings,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error creating user: {e}")
        return None

def update_user(db: Session, user_id: int, user_in: UserUpdate) -> Optional[User]:
    """
    Обновить пользователя по ID.
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return None
    try:
        for field, value in user_in.dict(exclude_unset=True).items():
            setattr(db_user, field, value)
        db.commit()
        db.refresh(db_user)
        return db_user
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error updating user: {e}")
        return None

def delete_user(db: Session, user_id: int) -> bool:
    """
    Удалить пользователя по ID.
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return False
    try:
        db.delete(db_user)
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error deleting user: {e}")
        return False 
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
import logging
from app.db.session import get_db
from app.schemas.user import UserCreate, UserRead, UserUpdate, UserList
from app.services import user_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=UserList)
def list_users(
    skip: int = Query(0, ge=0, description="Сколько записей пропустить"),
    limit: int = Query(100, ge=1, le=500, description="Максимум записей на страницу"),
    db: Session = Depends(get_db)
) -> UserList:
    """
    Получить список пользователей с пагинацией.
    """
    items, total = user_service.get_users(db, skip=skip, limit=limit)
    page = (skip // limit) + 1 if limit else 1
    pages = (total + limit - 1) // limit if limit else 1
    return UserList(items=items, total=total, page=page, size=limit, pages=pages)

@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)) -> UserRead:
    """
    Получить пользователя по ID.
    """
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        logger.warning(f"User {user_id} not found.")
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    """
    Создать нового пользователя.
    """
    user = user_service.create_user(db, user_in)
    return user

@router.put("/{user_id}", response_model=UserRead)
def update_user(user_id: int, user_in: UserUpdate, db: Session = Depends(get_db)) -> UserRead:
    """
    Обновить пользователя по ID.
    """
    user = user_service.update_user(db, user_id, user_in)
    if not user:
        logger.warning(f"User {user_id} not found for update.")
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)) -> None:
    """
    Удалить пользователя по ID.
    """
    success = user_service.delete_user(db, user_id)
    if not success:
        logger.warning(f"User {user_id} not found for delete.")
        raise HTTPException(status_code=404, detail="User not found") 
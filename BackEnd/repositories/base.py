"""
Generic base repository — provides CRUD operations for any SQLAlchemy model.
"""

from __future__ import annotations

from typing import Generic, TypeVar, Type, Optional, Any

from sqlalchemy.orm import Session

from models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Thin data-access layer. Routes must not contain raw SQL."""

    def __init__(self, model: Type[ModelT], db: Session):
        self._model = model
        self._db = db

    def get_by_id(self, record_id: int) -> Optional[ModelT]:
        return self._db.get(self._model, record_id)

    def get_all(self, limit: int = 100, offset: int = 0) -> list[ModelT]:
        return self._db.query(self._model).offset(offset).limit(limit).all()

    def create(self, **kwargs: Any) -> ModelT:
        instance = self._model(**kwargs)
        self._db.add(instance)
        self._db.commit()
        self._db.refresh(instance)
        return instance

    def update(self, instance: ModelT, **kwargs: Any) -> ModelT:
        for key, value in kwargs.items():
            setattr(instance, key, value)
        self._db.commit()
        self._db.refresh(instance)
        return instance

    def delete(self, instance: ModelT) -> None:
        self._db.delete(instance)
        self._db.commit()

    def count(self) -> int:
        return self._db.query(self._model).count()

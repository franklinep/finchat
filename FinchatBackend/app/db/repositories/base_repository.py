from __future__ import annotations

from typing import Generic, Optional, Type, TypeVar

from sqlalchemy.orm import Session

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, session: Session):
        self.session = session

    def add(self, entity: ModelType) -> ModelType:
        self.session.add(entity)
        return entity

    def get(self, model: Type[ModelType], entity_id: int) -> Optional[ModelType]:
        return self.session.get(model, entity_id)

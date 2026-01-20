from sqlalchemy.orm import Session

from app.domain.example import Example
from app.domain.repositories.example_repository import IExampleRepository
from app.infrastructure.database.models import ExampleModel


class ExampleRepository(IExampleRepository):
    """サンプルリポジトリ"""

    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, example_id: int) -> Example | None:
        """IDでエンティティを取得"""
        model = self.db.query(ExampleModel).filter(ExampleModel.id == example_id).first()
        if model is None:
            return None
        return self._to_entity(model)

    def find_all(self) -> list[Example]:
        """全エンティティを取得"""
        models = self.db.query(ExampleModel).all()
        return [self._to_entity(m) for m in models]

    def save(self, example: Example) -> Example:
        """エンティティを保存"""
        model = ExampleModel(
            name=example.name,
            description=example.description,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def _to_entity(self, model: ExampleModel) -> Example:
        """モデルをエンティティに変換"""
        return Example(
            id=model.id,
            name=model.name,
            description=model.description,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

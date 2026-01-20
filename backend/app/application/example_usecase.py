from datetime import datetime

from app.domain.example import Example
from app.domain.repositories.example_repository import IExampleRepository
from app.schemas.example import ExampleCreate


class ExampleUseCase:
    """サンプルユースケース"""

    def __init__(self, repository: IExampleRepository):
        self.repository = repository

    def create_example(self, data: ExampleCreate) -> Example:
        """サンプル作成"""
        # ドメインエンティティ生成は簡略化
        example = Example(
            id=0,  # DBで自動採番
            name=data.name,
            description=data.description,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        return self.repository.save(example)

    def get_example(self, example_id: int) -> Example | None:
        """サンプル取得"""
        return self.repository.find_by_id(example_id)

    def list_examples(self) -> list[Example]:
        """サンプル一覧"""
        return self.repository.find_all()

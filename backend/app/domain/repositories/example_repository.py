from abc import ABC, abstractmethod

from app.domain.example import Example


class IExampleRepository(ABC):
    """Exampleリポジトリのインターフェース"""

    @abstractmethod
    def find_by_id(self, example_id: int) -> Example | None:
        """IDでエンティティを取得"""
        pass

    @abstractmethod
    def find_all(self) -> list[Example]:
        """全エンティティを取得"""
        pass

    @abstractmethod
    def save(self, example: Example) -> Example:
        """エンティティを保存"""
        pass

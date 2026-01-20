from app.domain.example import Example
from app.domain.repositories.example_repository import IExampleRepository


class MockExampleRepository(IExampleRepository):
    """テスト用モックリポジトリ（インメモリ実装）"""

    def __init__(self):
        self.examples: dict[int, Example] = {}
        self.next_id = 1

    def find_by_id(self, example_id: int) -> Example | None:
        """IDでエンティティを取得"""
        return self.examples.get(example_id)

    def find_all(self) -> list[Example]:
        """全エンティティを取得"""
        return list(self.examples.values())

    def save(self, example: Example) -> Example:
        """エンティティを保存"""
        if example.id == 0:
            # 新規作成
            example.id = self.next_id
            self.next_id += 1
        self.examples[example.id] = example
        return example

    def clear(self):
        """テストデータをクリア（テスト用ヘルパー）"""
        self.examples = {}
        self.next_id = 1

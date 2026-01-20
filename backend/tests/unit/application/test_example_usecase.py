import pytest
from datetime import datetime

from app.application.example_usecase import ExampleUseCase
from app.domain.example import Example
from app.schemas.example import ExampleCreate
from tests.unit.mocks.mock_example_repository import MockExampleRepository


class TestExampleUseCase:
    """ExampleUseCaseのユニットテスト"""

    def setup_method(self):
        """各テストメソッド実行前に呼ばれる"""
        self.mock_repo = MockExampleRepository()
        self.usecase = ExampleUseCase(self.mock_repo)

    def test_create_example_success(self):
        """サンプル作成の正常系テスト"""
        data = ExampleCreate(name="Test Example", description="Test Description")

        result = self.usecase.create_example(data)

        assert result.id == 1  # 自動採番
        assert result.name == "Test Example"
        assert result.description == "Test Description"
        assert isinstance(result.created_at, datetime)
        assert isinstance(result.updated_at, datetime)

    def test_create_example_saves_to_repository(self):
        """サンプル作成時にリポジトリに保存される"""
        data = ExampleCreate(name="Test Example", description="Test Description")

        self.usecase.create_example(data)

        # リポジトリにデータが保存されていることを確認
        saved_examples = self.mock_repo.find_all()
        assert len(saved_examples) == 1
        assert saved_examples[0].name == "Test Example"

    def test_create_multiple_examples(self):
        """複数のサンプルを作成できる"""
        data1 = ExampleCreate(name="Example 1")
        data2 = ExampleCreate(name="Example 2")

        result1 = self.usecase.create_example(data1)
        result2 = self.usecase.create_example(data2)

        assert result1.id == 1
        assert result2.id == 2
        assert len(self.mock_repo.find_all()) == 2

    def test_get_example_success(self):
        """サンプル取得の正常系テスト"""
        # 事前にデータを作成
        created = self.usecase.create_example(ExampleCreate(name="Test"))

        # 取得
        result = self.usecase.get_example(created.id)

        assert result is not None
        assert result.id == created.id
        assert result.name == "Test"

    def test_get_example_not_found(self):
        """存在しないIDでの取得はNoneを返す"""
        result = self.usecase.get_example(999)

        assert result is None

    def test_list_examples_empty(self):
        """データがない場合は空リストを返す"""
        result = self.usecase.list_examples()

        assert result == []

    def test_list_examples_with_data(self):
        """複数データの一覧取得"""
        self.usecase.create_example(ExampleCreate(name="Example 1"))
        self.usecase.create_example(ExampleCreate(name="Example 2"))
        self.usecase.create_example(ExampleCreate(name="Example 3"))

        result = self.usecase.list_examples()

        assert len(result) == 3
        assert result[0].name == "Example 1"
        assert result[1].name == "Example 2"
        assert result[2].name == "Example 3"

    def test_create_example_without_description(self):
        """descriptionなしでの作成"""
        data = ExampleCreate(name="Test Example")

        result = self.usecase.create_example(data)

        assert result.name == "Test Example"
        assert result.description is None

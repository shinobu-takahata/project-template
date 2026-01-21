import pytest
from datetime import UTC, datetime

from app.domain.example import Example


class TestExample:
    """Exampleエンティティのユニットテスト"""

    def test_create_example(self):
        """エンティティ生成のテスト"""
        now = datetime.now(UTC)
        example = Example(
            id=1,
            name="Test",
            description="Test Description",
            created_at=now,
            updated_at=now,
        )
        assert example.id == 1
        assert example.name == "Test"
        assert example.description == "Test Description"

    def test_update_name_success(self):
        """名前更新の正常系テスト"""
        now = datetime.now(UTC)
        example = Example(
            id=1, name="Old Name", description=None, created_at=now, updated_at=now
        )

        example.update_name("New Name")

        assert example.name == "New Name"
        assert example.updated_at > now  # updated_atが更新されている

    def test_update_name_with_empty_string_raises_error(self):
        """空文字列での名前更新は失敗する"""
        now = datetime.now(UTC)
        example = Example(
            id=1, name="Old Name", description=None, created_at=now, updated_at=now
        )

        with pytest.raises(ValueError, match="Name cannot be empty"):
            example.update_name("")

    def test_update_name_with_whitespace_only_raises_error(self):
        """空白文字のみでの名前更新は失敗する"""
        now = datetime.now(UTC)
        example = Example(
            id=1, name="Old Name", description=None, created_at=now, updated_at=now
        )

        with pytest.raises(ValueError, match="Name cannot be empty"):
            example.update_name("   ")

    def test_update_name_preserves_other_fields(self):
        """名前更新時に他のフィールドは保持される"""
        now = datetime.now(UTC)
        example = Example(
            id=1,
            name="Old Name",
            description="Description",
            created_at=now,
            updated_at=now,
        )

        example.update_name("New Name")

        assert example.id == 1
        assert example.description == "Description"
        assert example.created_at == now  # created_atは変更されない

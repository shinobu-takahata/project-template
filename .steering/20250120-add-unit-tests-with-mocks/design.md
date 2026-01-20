# 設計：ユニットテストのモック化実装

## 実装アプローチ

### 1. テストピラミッドの実現

```
┌─────────────────────────────────┐
│  tests/unit/domain/             │  Domain層のユニットテスト
│  - test_example.py              │  ドメインロジックの検証
│  （最速・モック不要）            │
├─────────────────────────────────┤
│  tests/unit/application/        │  Application層のユニットテスト
│  - test_example_usecase.py      │  ビジネスフロー検証
│  （高速・モックリポジトリ使用）  │
├─────────────────────────────────┤
│  tests/unit/mocks/              │  テスト用モック
│  - mock_example_repository.py   │
├─────────────────────────────────┤
│  tests/integration/             │  統合テスト
│  - test_examples.py（既存移動） │  API全体の動作検証
│  - test_health.py（既存移動）   │  （実DB使用）
└─────────────────────────────────┘
```

### 2. テストの種類と責務

#### Domain層のユニットテスト
- **対象**：`Example` エンティティ
- **検証内容**：ドメインロジック（`update_name` メソッド）
- **依存**：なし（純粋な関数テスト）
- **実行速度**：最速

#### Application層のユニットテスト
- **対象**：`ExampleUseCase`
- **検証内容**：ビジネスフロー・オーケストレーション
- **依存**：モックリポジトリ（DB不要）
- **実行速度**：高速

#### 統合テスト（既存）
- **対象**：API層全体
- **検証内容**：システム全体の動作
- **依存**：実DB（SQLite）
- **実行速度**：中速

## 変更するコンポーネント

### 1. モックリポジトリの作成

#### `tests/unit/mocks/mock_example_repository.py`

```python
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
```

**設計のポイント：**
- `IExampleRepository` を実装（型の互換性保証）
- インメモリデータストア（`dict`）を使用
- DB接続不要で高速
- `clear()` メソッドでテストデータのリセットが容易

### 2. Domain層のユニットテスト

#### `tests/unit/domain/test_example.py`

```python
import pytest
from datetime import datetime

from app.domain.example import Example


class TestExample:
    """Exampleエンティティのユニットテスト"""

    def test_create_example(self):
        """エンティティ生成のテスト"""
        now = datetime.utcnow()
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
        now = datetime.utcnow()
        example = Example(
            id=1, name="Old Name", description=None, created_at=now, updated_at=now
        )

        example.update_name("New Name")

        assert example.name == "New Name"
        assert example.updated_at > now  # updated_atが更新されている

    def test_update_name_with_empty_string_raises_error(self):
        """空文字列での名前更新は失敗する"""
        now = datetime.utcnow()
        example = Example(
            id=1, name="Old Name", description=None, created_at=now, updated_at=now
        )

        with pytest.raises(ValueError, match="Name cannot be empty"):
            example.update_name("")

    def test_update_name_with_whitespace_only_raises_error(self):
        """空白文字のみでの名前更新は失敗する"""
        now = datetime.utcnow()
        example = Example(
            id=1, name="Old Name", description=None, created_at=now, updated_at=now
        )

        with pytest.raises(ValueError, match="Name cannot be empty"):
            example.update_name("   ")

    def test_update_name_preserves_other_fields(self):
        """名前更新時に他のフィールドは保持される"""
        now = datetime.utcnow()
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
```

**テストの特徴：**
- ドメインロジックのバリデーションを検証
- 外部依存なし（最速）
- エッジケースのテスト（空文字、空白のみ）

### 3. Application層のユニットテスト

#### `tests/unit/application/test_example_usecase.py`

```python
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
```

**テストの特徴：**
- モックリポジトリを使用（DB不要）
- ビジネスフローの検証
- setup_method で各テストの独立性を保証

### 4. ディレクトリ構造の変更

**変更前：**
```
tests/
├── __init__.py
├── conftest.py
├── test_examples.py
└── test_health.py
```

**変更後：**
```
tests/
├── __init__.py
├── conftest.py (統合テスト用として維持)
├── unit/
│   ├── __init__.py
│   ├── domain/
│   │   ├── __init__.py
│   │   └── test_example.py
│   ├── application/
│   │   ├── __init__.py
│   │   └── test_example_usecase.py
│   └── mocks/
│       ├── __init__.py
│       └── mock_example_repository.py
└── integration/
    ├── __init__.py
    ├── conftest.py (統合テスト用の設定をここに移動)
    ├── test_examples.py (既存から移動)
    └── test_health.py (既存から移動)
```

### 5. conftest.pyの分離

#### `tests/integration/conftest.py` (新規作成)

既存の `tests/conftest.py` の内容を移動：
```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app

# テスト用インメモリDB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
```

#### `tests/conftest.py` (ルート)

ユニットテスト用の共通設定（必要に応じて追加）：
```python
# ユニットテスト用の共通設定
# 現時点では特に必要なfixtureはないが、将来的に追加可能
```

## 影響範囲の分析

### 新規作成ファイル（9ファイル）
1. `tests/unit/__init__.py`
2. `tests/unit/domain/__init__.py`
3. `tests/unit/domain/test_example.py`
4. `tests/unit/application/__init__.py`
5. `tests/unit/application/test_example_usecase.py`
6. `tests/unit/mocks/__init__.py`
7. `tests/unit/mocks/mock_example_repository.py`
8. `tests/integration/__init__.py`
9. `tests/integration/conftest.py`

### 移動ファイル（2ファイル）
1. `tests/test_examples.py` → `tests/integration/test_examples.py`
2. `tests/test_health.py` → `tests/integration/test_health.py`

### 変更ファイル
1. `tests/conftest.py` - 統合テスト設定を `tests/integration/conftest.py` に移動

### 変更不要
- Application層のコード
- Domain層のコード
- Infrastructure層のコード

## テスト実行コマンド

### 全テスト実行
```bash
pytest
```

### ユニットテストのみ実行（高速）
```bash
pytest tests/unit/
```

### Domain層のみ
```bash
pytest tests/unit/domain/
```

### Application層のみ
```bash
pytest tests/unit/application/
```

### 統合テストのみ実行
```bash
pytest tests/integration/
```

### カバレッジ付きで実行
```bash
pytest --cov=app --cov-report=html
```

## 期待される効果

### 1. テスト実行速度の比較

**Before（統合テストのみ）：**
```bash
$ pytest
======================== 3 passed in 2.45s ========================
```

**After（ユニットテスト追加）：**
```bash
$ pytest tests/unit/
======================== 15 passed in 0.12s ========================

$ pytest tests/integration/
======================== 3 passed in 2.45s ========================

$ pytest
======================== 18 passed in 2.57s ========================
```

### 2. 開発フィードバックループの改善

**従来：**
- コード変更 → 統合テスト実行（2-3秒） → 結果確認

**改善後：**
- コード変更 → ユニットテスト実行（< 0.2秒） → 高速フィードバック
- 必要に応じて統合テスト実行

### 3. テストカバレッジの向上

- Domain層のロジックを直接テスト
- Application層のビジネスフローを独立してテスト
- エッジケースのテストが容易

## リスクと対策

### リスク1: 既存テストの移動による影響
**対策：**
- 統合テストの内容は変更せず、ディレクトリのみ移動
- 移動後に統合テストを実行して動作確認

### リスク2: モックと実装の乖離
**対策：**
- モックは `IExampleRepository` を実装（型で保証）
- 統合テストで実装との整合性を検証

### リスク3: テスト保守コストの増加
**対策：**
- モックは共通化（`tests/unit/mocks/`）
- 明確な責務分離でテストの目的を明確化

## 実装の優先順位

### Phase 1: ディレクトリ構造とモック作成
1. テストディレクトリ構造作成
2. モックリポジトリ作成
3. 既存テストの移動

### Phase 2: Domain層のユニットテスト
1. `test_example.py` 作成
2. ドメインロジックのテスト

### Phase 3: Application層のユニットテスト
1. `test_example_usecase.py` 作成
2. ビジネスフローのテスト

### Phase 4: 動作確認
1. 全テスト実行
2. カバレッジ確認

## まとめ

この変更により、テストピラミッドが実現され、以下が可能になる：
- **高速なフィードバック**：ユニットテストで即座に問題検出
- **独立したテスト**：各レイヤーを独立してテスト
- **テスト容易性**：モックによりDB不要のテスト
- **保守性の向上**：明確な責務分離

前回の依存性注入の改善が真価を発揮する。

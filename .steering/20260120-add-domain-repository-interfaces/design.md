# 設計：Domain層へのRepositoryインターフェース追加

## 実装アプローチ

### 1. 依存性逆転の原則（DIP）の適用
現在の依存関係を以下のように変更する：

**変更前：**
```
Application Layer (ExampleUseCase)
    ↓ 直接依存
Infrastructure Layer (ExampleRepository)
```

**変更後：**
```
Application Layer (ExampleUseCase)
    ↓ 依存
Domain Layer (IExampleRepository - Interface)
    ↑ 実装
Infrastructure Layer (ExampleRepository)
```

### 2. Pythonの抽象基底クラス（ABC）を使用
- `abc.ABC` と `abc.abstractmethod` を使用してインターフェースを定義
- 型ヒントを活用し、mypyでの静的型チェックに対応

## 変更するコンポーネント

### 1. Domain層 - 新規作成

#### `app/domain/repositories/__init__.py`
リポジトリインターフェースをエクスポート

#### `app/domain/repositories/example_repository.py`
```python
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
```

**設計ポイント：**
- インターフェース名は `I` プレフィックスを使用（Python慣習）
- データベースやSQLAlchemyへの依存を一切含めない
- ドメインエンティティ（`Example`）のみに依存
- メソッドシグネチャのみを定義

### 2. Infrastructure層 - 修正

#### `app/infrastructure/repositories/example_repository.py`
```python
from sqlalchemy.orm import Session

from app.domain.example import Example
from app.domain.repositories.example_repository import IExampleRepository
from app.infrastructure.database.models import ExampleModel


class ExampleRepository(IExampleRepository):
    """Exampleリポジトリの実装（SQLAlchemy）"""

    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, example_id: int) -> Example | None:
        # 既存実装を維持
        ...

    def find_all(self) -> list[Example]:
        # 既存実装を維持
        ...

    def save(self, example: Example) -> Example:
        # 既存実装を維持
        ...
```

**変更点：**
- `IExampleRepository` を継承
- 実装内容は既存のまま維持

### 3. Application層 - 修正

#### `app/application/example_usecase.py`
```python
from datetime import datetime
from sqlalchemy.orm import Session

from app.domain.example import Example
from app.domain.repositories.example_repository import IExampleRepository
from app.infrastructure.repositories.example_repository import ExampleRepository
from app.schemas.example import ExampleCreate


class ExampleUseCase:
    """サンプルユースケース"""

    def __init__(self, db: Session):
        # インターフェースに依存するが、具象クラスを注入
        self.repository: IExampleRepository = ExampleRepository(db)

    # メソッドは既存のまま維持
```

**変更点：**
- import文で `IExampleRepository` をインポート
- 型アノテーションで `self.repository: IExampleRepository` と宣言
- 実際の動作は変わらないが、型システム上はインターフェースに依存

**将来的な改善案（今回は実装しない）：**
```python
class ExampleUseCase:
    def __init__(self, repository: IExampleRepository):
        self.repository = repository
```
この形式にすれば、DIコンテナを使った完全な依存性注入が可能になる。

### 4. API層 - 影響確認

#### `app/api/v1/endpoints/examples.py`
- 変更不要
- `ExampleUseCase(db)` の呼び出しは既存のまま動作

## データ構造の変更

データ構造の変更はなし。以下は変更されない：
- `Example` エンティティ（[example.py](backend/app/domain/example.py)）
- `ExampleModel`（[models.py](backend/app/infrastructure/database/models.py)）
- `ExampleCreate`, `ExampleResponse` スキーマ（[example.py](backend/app/schemas/example.py)）

## 影響範囲の分析

### 変更が必要なファイル
1. **新規作成**
   - `app/domain/repositories/__init__.py`
   - `app/domain/repositories/example_repository.py`

2. **修正必要**
   - `app/infrastructure/repositories/example_repository.py` - インターフェース継承を追加
   - `app/application/example_usecase.py` - import文と型アノテーション修正

3. **変更不要**
   - `app/api/v1/endpoints/examples.py` - 動作確認のみ
   - `app/domain/example.py`
   - `app/infrastructure/database/models.py`
   - `app/schemas/example.py`

### 依存関係の整理

**変更後の依存関係：**
```
┌─────────────────────────────────────┐
│        API Layer (FastAPI)          │
│    app/api/v1/endpoints/            │
└─────────────┬───────────────────────┘
              │ depends on
              ↓
┌─────────────────────────────────────┐
│      Application Layer              │
│    app/application/                 │
│    - ExampleUseCase                 │
└─────────────┬───────────────────────┘
              │ depends on
              ↓
┌─────────────────────────────────────┐
│       Domain Layer                  │
│    app/domain/                      │
│    - Example (Entity)               │
│    - IExampleRepository (Interface) │
└─────────────┬───────────────────────┘
              │ implemented by
              ↑
┌─────────────────────────────────────┐
│    Infrastructure Layer             │
│    app/infrastructure/              │
│    - ExampleRepository (Impl)       │
│    - ExampleModel (SQLAlchemy)      │
└─────────────────────────────────────┘
```

### テスト容易性の向上
この変更により、以下が可能になる：
- `ExampleUseCase` のユニットテストでモックリポジトリを使用可能
- インメモリリポジトリの実装による高速テスト
- データベース接続なしでのビジネスロジックテスト

## リスクと対策

### リスク1: 既存動作の破壊
**対策：**
- 実装内容は変更せず、型定義とインターフェースのみ追加
- API層での動作確認テストを実施

### リスク2: 循環importの発生
**対策：**
- domain層は他のレイヤーをimportしない（純粋な依存）
- infrastructure層のみがdomain層をimportする

### リスク3: 型チェックエラー
**対策：**
- 適切な型アノテーションを使用
- 必要に応じてmypyで検証

## 永続的ドキュメントへの影響

### 更新が必要なドキュメント
現時点では以下のドキュメントが存在しない可能性があるため、実装後に確認：
- `docs/architecture.md` - レイヤードアーキテクチャとDIPの説明を追加
- `docs/repository-structure.md` - domain/repositories/ の追加を反映

## 実装の優先順位

1. **Phase 1: インターフェース定義**
   - domain層のディレクトリとインターフェース作成

2. **Phase 2: Infrastructure層の修正**
   - ExampleRepository にインターフェース実装を追加

3. **Phase 3: Application層の修正**
   - ExampleUseCase のimportと型アノテーション修正

4. **Phase 4: 動作確認**
   - APIエンドポイントの動作確認
   - 既存機能が正常に動作することを確認

## 今後の拡張性

この変更により、以下の拡張が容易になる：
- 新しいリポジトリの追加（パターンが確立）
- DIコンテナの導入（将来的な改善）
- テストダブルの作成（モック、スタブ、フェイク）
- 異なるデータソースへの切り替え（例：NoSQL、外部API）

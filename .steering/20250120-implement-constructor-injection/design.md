# 設計：完全な依存性注入（Constructor Injection）の実装

## 実装アプローチ

### 1. 依存性注入パターンの適用
Constructor Injection（コンストラクタインジェクション）パターンを採用し、以下の原則に従う：

**依存性注入の3原則：**
1. **高レベルモジュールは低レベルモジュールに依存しない** - 両方とも抽象に依存する
2. **抽象は詳細に依存しない** - 詳細が抽象に依存する
3. **依存はコンストラクタで注入される** - 生成ロジックと使用ロジックを分離

**責務の分離：**
- **Application層**：ビジネスロジックの実行（依存の使用）
- **API層**：依存の解決と注入（依存の生成）

### 2. レイヤー間の依存関係

**変更後のアーキテクチャ：**
```
┌────────────────────────────────────────────┐
│         API Layer (FastAPI)                │
│   - Dependency Resolution（依存解決）       │
│   - Repository Instantiation（生成）       │
│   - UseCase Instantiation（生成）          │
└────────────────┬───────────────────────────┘
                 │ creates & injects
                 ↓
┌────────────────────────────────────────────┐
│       Application Layer                    │
│   - ExampleUseCase                         │
│   - Business Logic（ビジネスロジック）      │
│   - Uses IExampleRepository（使用のみ）    │
└────────────────┬───────────────────────────┘
                 │ depends on (interface)
                 ↓
┌────────────────────────────────────────────┐
│        Domain Layer                        │
│   - IExampleRepository (Interface)         │
│   - Example (Entity)                       │
└────────────────┬───────────────────────────┘
                 │ implemented by
                 ↑
┌────────────────────────────────────────────┐
│     Infrastructure Layer                   │
│   - ExampleRepository (Implementation)     │
│   - ExampleModel (SQLAlchemy)              │
└────────────────────────────────────────────┘
```

## 変更するコンポーネント

### 1. Application層 - 修正

#### `app/application/example_usecase.py`

**変更前：**
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
        self.repository: IExampleRepository = ExampleRepository(db)
```

**変更後：**
```python
from datetime import datetime

from app.domain.example import Example
from app.domain.repositories.example_repository import IExampleRepository
from app.schemas.example import ExampleCreate


class ExampleUseCase:
    """サンプルユースケース"""

    def __init__(self, repository: IExampleRepository):
        self.repository = repository
```

**変更点：**
1. `sqlalchemy.orm.Session` のimportを削除
2. `app.infrastructure.repositories.example_repository.ExampleRepository` のimportを削除
3. コンストラクタパラメータを `db: Session` から `repository: IExampleRepository` に変更
4. リポジトリのインスタンス化ロジックを削除
5. 受け取ったリポジトリをそのまま代入

**設計のポイント：**
- Application層がInfrastructure層を一切知らない（完全な疎結合）
- Domain層のインターフェースのみに依存
- ビジネスロジックに集中できる
- テスト時にモックを簡単に注入可能

### 2. API層 - 修正

#### `app/api/v1/endpoints/examples.py`

**変更前：**
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.application.example_usecase import ExampleUseCase
from app.core.database import get_db
from app.schemas.example import ExampleCreate, ExampleResponse

router = APIRouter()


@router.post("/", response_model=ExampleResponse, status_code=201)
async def create_example(data: ExampleCreate, db: Session = Depends(get_db)):
    """サンプル作成"""
    usecase = ExampleUseCase(db)
    example = usecase.create_example(data)
    return example
```

**変更後：**
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.application.example_usecase import ExampleUseCase
from app.core.database import get_db
from app.infrastructure.repositories.example_repository import ExampleRepository
from app.schemas.example import ExampleCreate, ExampleResponse

router = APIRouter()


@router.post("/", response_model=ExampleResponse, status_code=201)
async def create_example(data: ExampleCreate, db: Session = Depends(get_db)):
    """サンプル作成"""
    repository = ExampleRepository(db)
    usecase = ExampleUseCase(repository)
    example = usecase.create_example(data)
    return example
```

**変更点：**
1. `ExampleRepository` をimport
2. エンドポイント内で `ExampleRepository` をインスタンス化
3. リポジトリを `ExampleUseCase` のコンストラクタに渡す

**この変更を全エンドポイントに適用：**
- `create_example` (POST /)
- `get_example` (GET /{example_id})
- `list_examples` (GET /)

### 3. 依存解決の流れ

**リクエスト処理のフロー：**
```
1. HTTPリクエスト受信
   ↓
2. FastAPI Depends: get_db() → Session取得
   ↓
3. API層: ExampleRepository(db) → リポジトリ生成
   ↓
4. API層: ExampleUseCase(repository) → ユースケース生成
   ↓
5. Application層: ビジネスロジック実行
   ↓
6. Domain層: エンティティ操作
   ↓
7. Infrastructure層: DB永続化
   ↓
8. レスポンス返却
```

## データ構造の変更

データ構造の変更はなし。以下は全て変更されない：
- `Example` エンティティ
- `IExampleRepository` インターフェース
- `ExampleRepository` 実装
- `ExampleModel` SQLAlchemyモデル
- スキーマ（`ExampleCreate`, `ExampleResponse`）

## 影響範囲の分析

### 変更が必要なファイル

1. **`app/application/example_usecase.py`**
   - import文の削除（Session, ExampleRepository）
   - コンストラクタシグネチャ変更
   - リポジトリインスタンス化ロジック削除

2. **`app/api/v1/endpoints/examples.py`**
   - import文追加（ExampleRepository）
   - 3つのエンドポイント全てで依存解決ロジック追加
     - `create_example` (Line 12-16)
     - `get_example` (Line 20-26)
     - `list_examples` (Line 30-34)

### 変更不要なファイル

- `app/domain/repositories/example_repository.py` - インターフェース定義
- `app/infrastructure/repositories/example_repository.py` - リポジトリ実装
- `app/domain/example.py` - エンティティ
- `app/infrastructure/database/models.py` - SQLAlchemyモデル
- `app/schemas/example.py` - Pydanticスキーマ
- `app/core/database.py` - DB接続設定

## テスト容易性の向上

### Before: テストが困難
```python
# Application層がInfrastructure層に依存している
usecase = ExampleUseCase(db)  # 必ずDBが必要
```

**問題点：**
- データベース接続が必須
- テストが遅い（I/O待ち）
- テストデータのセットアップが複雑
- 統合テストにしかならない

### After: ユニットテストが可能
```python
# モックリポジトリを簡単に注入
class MockExampleRepository(IExampleRepository):
    def __init__(self):
        self.saved_examples = []

    def find_by_id(self, example_id: int) -> Example | None:
        return next((e for e in self.saved_examples if e.id == example_id), None)

    def find_all(self) -> list[Example]:
        return self.saved_examples.copy()

    def save(self, example: Example) -> Example:
        self.saved_examples.append(example)
        return example


def test_create_example():
    # Arrange
    mock_repo = MockExampleRepository()
    usecase = ExampleUseCase(mock_repo)
    data = ExampleCreate(name="Test", description="Test Description")

    # Act
    result = usecase.create_example(data)

    # Assert
    assert result.name == "Test"
    assert len(mock_repo.saved_examples) == 1
```

**メリット：**
- データベース不要（高速）
- テストが独立（副作用なし）
- エッジケースのテストが容易
- 真のユニットテスト

## 将来的な拡張性

### 1. FastAPI Dependsを使った高度なDI（将来的オプション）

現在は手動DIだが、将来的にFastAPIのDependsを活用してさらに洗練させることも可能：

```python
# 依存関数の定義
def get_example_repository(db: Session = Depends(get_db)) -> IExampleRepository:
    return ExampleRepository(db)

def get_example_usecase(
    repository: IExampleRepository = Depends(get_example_repository)
) -> ExampleUseCase:
    return ExampleUseCase(repository)

# エンドポイント
@router.post("/", response_model=ExampleResponse, status_code=201)
async def create_example(
    data: ExampleCreate,
    usecase: ExampleUseCase = Depends(get_example_usecase)
):
    example = usecase.create_example(data)
    return example
```

ただし、今回はシンプルさを優先し、この拡張は実施しない。

### 2. DIコンテナの導入（将来的オプション）

さらに複雑になった場合は、`dependency-injector` などのライブラリ導入も検討可能。

## リスクと対策

### リスク1: エンドポイントのコード量増加
**影響：**
各エンドポイントで依存解決のコードが2行増える

**対策：**
- 現時点では許容範囲
- 将来的にはFastAPI Dependsで抽象化可能

**評価：**
低リスク - コードは増えるが、可読性と保守性が向上

### リスク2: 既存動作の破壊
**影響：**
コンストラクタシグネチャ変更により、呼び出し側の修正が必要

**対策：**
- API層のみが `ExampleUseCase` を使用しているため、影響範囲は限定的
- 全エンドポイントを同時に修正
- 修正後に動作確認テストを実施

**評価：**
低リスク - 影響範囲が明確で、修正箇所も少ない

### リスク3: パフォーマンスへの影響
**影響：**
各リクエストでリポジトリとユースケースをインスタンス化

**対策：**
- 既存実装も毎回インスタンス化しているため、パフォーマンス変化なし
- むしろ、ステートレスで明確になる

**評価：**
影響なし

## 実装の優先順位

### Phase 1: Application層の修正
1. `example_usecase.py` のimport文削除
2. コンストラクタシグネチャ変更
3. インスタンス化ロジック削除

### Phase 2: API層の修正
1. `examples.py` にimport追加
2. `create_example` エンドポイント修正
3. `get_example` エンドポイント修正
4. `list_examples` エンドポイント修正

### Phase 3: 動作確認
1. 構文チェック
2. APIエンドポイントの動作確認（全3エンドポイント）
3. エラーが発生しないことを確認

### Phase 4: ドキュメント更新（オプション）
1. タスクリストの更新
2. 永続的ドキュメントへの反映検討

## 期待される効果

### 1. テスト容易性の大幅向上
- ユニットテストでDB接続不要
- モックを簡単に注入可能
- テスト実行速度の向上

### 2. 依存関係の明確化
- レイヤー間の責務が明確
- Application層がインフラから完全に独立

### 3. 保守性の向上
- ビジネスロジックとインフラの分離
- リポジトリ実装の差し替えが容易

### 4. DDDとクリーンアーキテクチャの実現
- 依存性逆転の原則（DIP）の完全な実現
- 関心の分離（SoC）の徹底

## まとめ

この変更により、前回追加したリポジトリインターフェースが真の価値を発揮する。Application層は完全にDomain層のみに依存し、Infrastructure層への依存がなくなる。これにより、テスト容易性、保守性、拡張性が大幅に向上する。

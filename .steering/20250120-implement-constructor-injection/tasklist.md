# タスクリスト：完全な依存性注入（Constructor Injection）の実装

## タスクの進捗状況

### Phase 1: Application層の修正
- [ ] `app/application/example_usecase.py` のimport文を削除
  - `from sqlalchemy.orm import Session` を削除
  - `from app.infrastructure.repositories.example_repository import ExampleRepository` を削除
- [ ] コンストラクタシグネチャを変更
  - `def __init__(self, db: Session):` を `def __init__(self, repository: IExampleRepository):` に変更
- [ ] リポジトリインスタンス化ロジックを削除
  - `self.repository: IExampleRepository = ExampleRepository(db)` を `self.repository = repository` に変更

### Phase 2: API層の修正
- [ ] `app/api/v1/endpoints/examples.py` にimport追加
  - `from app.infrastructure.repositories.example_repository import ExampleRepository` を追加
- [ ] `create_example` エンドポイントを修正（POST /）
  - リポジトリをインスタンス化
  - リポジトリをユースケースに注入
- [ ] `get_example` エンドポイントを修正（GET /{example_id}）
  - リポジトリをインスタンス化
  - リポジトリをユースケースに注入
- [ ] `list_examples` エンドポイントを修正（GET /）
  - リポジトリをインスタンス化
  - リポジトリをユースケースに注入

### Phase 3: 動作確認
- [ ] Python構文チェック実行
- [ ] Dockerコンテナの状態確認
- [ ] POST /api/v1/examples/ のテスト（サンプル作成）
- [ ] GET /api/v1/examples/{id} のテスト（サンプル取得）
- [ ] GET /api/v1/examples/ のテスト（サンプル一覧取得）
- [ ] エラーが発生しないことを確認

### Phase 4: ステアリングファイル更新
- [ ] tasklist.mdを更新して完了状態を記録

## 完了条件

### 機能的完了条件
1. `ExampleUseCase` が `ExampleRepository` をimportしていない
2. `ExampleUseCase` が `Session` をimportしていない
3. `ExampleUseCase` のコンストラクタが `IExampleRepository` を受け取る
4. API層の全エンドポイントで依存解決が実装されている
5. 既存のAPIが正常に動作する

### 技術的完了条件
1. Pythonのインポートエラーが発生しない
2. 型アノテーションが正しく設定されている
3. Application層がInfrastructure層に依存していない
4. 依存関係が以下の方向になっている：
   ```
   api → application → domain ← infrastructure
   ```

## 各タスクの詳細

### Task 1.1-1.3: Application層の修正

ファイル: `backend/app/application/example_usecase.py`

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

### Task 2.1: API層のimport追加

ファイル: `backend/app/api/v1/endpoints/examples.py`

**追加するimport：**
```python
from app.infrastructure.repositories.example_repository import ExampleRepository
```

### Task 2.2: create_example エンドポイント修正

**変更前（Line 12-16）：**
```python
@router.post("/", response_model=ExampleResponse, status_code=201)
async def create_example(data: ExampleCreate, db: Session = Depends(get_db)):
    """サンプル作成"""
    usecase = ExampleUseCase(db)
    example = usecase.create_example(data)
    return example
```

**変更後：**
```python
@router.post("/", response_model=ExampleResponse, status_code=201)
async def create_example(data: ExampleCreate, db: Session = Depends(get_db)):
    """サンプル作成"""
    repository = ExampleRepository(db)
    usecase = ExampleUseCase(repository)
    example = usecase.create_example(data)
    return example
```

### Task 2.3: get_example エンドポイント修正

**変更前（Line 20-26）：**
```python
@router.get("/{example_id}", response_model=ExampleResponse)
async def get_example(example_id: int, db: Session = Depends(get_db)):
    """サンプル取得"""
    usecase = ExampleUseCase(db)
    example = usecase.get_example(example_id)
    if example is None:
        raise HTTPException(status_code=404, detail="Example not found")
    return example
```

**変更後：**
```python
@router.get("/{example_id}", response_model=ExampleResponse)
async def get_example(example_id: int, db: Session = Depends(get_db)):
    """サンプル取得"""
    repository = ExampleRepository(db)
    usecase = ExampleUseCase(repository)
    example = usecase.get_example(example_id)
    if example is None:
        raise HTTPException(status_code=404, detail="Example not found")
    return example
```

### Task 2.4: list_examples エンドポイント修正

**変更前（Line 30-34）：**
```python
@router.get("/", response_model=list[ExampleResponse])
async def list_examples(db: Session = Depends(get_db)):
    """サンプル一覧"""
    usecase = ExampleUseCase(db)
    examples = usecase.list_examples()
    return examples
```

**変更後：**
```python
@router.get("/", response_model=list[ExampleResponse])
async def list_examples(db: Session = Depends(get_db)):
    """サンプル一覧"""
    repository = ExampleRepository(db)
    usecase = ExampleUseCase(repository)
    examples = usecase.list_examples()
    return examples
```

### Task 3.1-3.6: 動作確認

**構文チェック：**
```bash
docker exec project-template-backend-1 python -m py_compile \
  app/application/example_usecase.py \
  app/api/v1/endpoints/examples.py
```

**APIテスト：**
```bash
# POSTテスト
curl -X POST http://localhost:8000/api/v1/examples/ \
  -H "Content-Type: application/json" \
  -d '{"name": "DI Test", "description": "Testing Constructor Injection"}'

# GETテスト（特定ID）
curl -X GET http://localhost:8000/api/v1/examples/1

# GETテスト（一覧）
curl -X GET http://localhost:8000/api/v1/examples/
```

## 注意事項

1. **順序厳守**
   - Application層を先に修正してからAPI層を修正
   - Application層修正後はAPI層が動かなくなるため、連続して作業する

2. **全エンドポイント修正**
   - 3つすべてのエンドポイントを同時に修正
   - 一部だけ修正すると動作しないエンドポイントが発生

3. **テストの重要性**
   - すべてのエンドポイントが正常に動作することを確認
   - 既存データでのテストも実施

## 期待される結果

### Before（現在）
- Application層がInfrastructure層に依存
- ユニットテストでモック注入が不可能
- DB接続なしでテストできない

### After（完了後）
- Application層がDomain層のみに依存
- ユニットテストでモック注入が可能
- DB接続なしでビジネスロジックをテスト可能
- 依存性逆転の原則（DIP）を完全に実現

## 関連ドキュメント

- [requirements.md](./requirements.md) - 要求内容の詳細
- [design.md](./design.md) - 設計の詳細とアーキテクチャ図
- [前回の作業](./../20250120-add-domain-repository-interfaces/) - リポジトリインターフェース追加

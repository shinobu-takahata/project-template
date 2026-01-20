# タスクリスト：Domain層へのRepositoryインターフェース追加

## タスクの進捗状況

### Phase 1: インターフェース定義
- [ ] `app/domain/repositories/` ディレクトリを作成
- [ ] `app/domain/repositories/__init__.py` を作成
- [ ] `app/domain/repositories/example_repository.py` を作成（IExampleRepositoryインターフェース）

### Phase 2: Infrastructure層の修正
- [ ] `app/infrastructure/repositories/example_repository.py` を修正
  - IExampleRepositoryを継承
  - 既存の実装を維持

### Phase 3: Application層の修正
- [ ] `app/application/example_usecase.py` を修正
  - IExampleRepositoryをimport
  - 型アノテーションを追加（self.repository: IExampleRepository）

### Phase 4: 動作確認
- [ ] Dockerコンテナを起動
- [ ] APIエンドポイントの動作確認
  - POST /api/v1/examples/ でサンプル作成
  - GET /api/v1/examples/{id} でサンプル取得
  - GET /api/v1/examples/ でサンプル一覧取得
- [ ] エラーが発生しないことを確認

### Phase 5: ドキュメント更新（オプション）
- [ ] `docs/architecture.md` の存在確認と更新検討
- [ ] `docs/repository-structure.md` の存在確認と更新検討

## 完了条件

### 機能的完了条件
1. domain層に `IExampleRepository` インターフェースが存在する
2. infrastructure層の `ExampleRepository` が `IExampleRepository` を実装している
3. application層の `ExampleUseCase` が `IExampleRepository` に型依存している
4. 既存のAPIが変更前と同じように動作する

### 技術的完了条件
1. Pythonのインポートエラーが発生しない
2. 型アノテーションが正しく設定されている
3. 依存関係が以下の方向になっている：
   ```
   api → application → domain ← infrastructure
   ```

## 各タスクの詳細

### Task 1.1: ディレクトリ作成
```bash
mkdir -p backend/app/domain/repositories
```

### Task 1.2: __init__.py 作成
ファイル: `backend/app/domain/repositories/__init__.py`
```python
from app.domain.repositories.example_repository import IExampleRepository

__all__ = ["IExampleRepository"]
```

### Task 1.3: インターフェース作成
ファイル: `backend/app/domain/repositories/example_repository.py`
- ABCを使用した抽象基底クラス
- find_by_id, find_all, save メソッドを抽象メソッドとして定義

### Task 2.1: Infrastructure層修正
ファイル: `backend/app/infrastructure/repositories/example_repository.py`
- IExampleRepository をimport
- class ExampleRepository(IExampleRepository) に変更
- 既存の実装コードは維持

### Task 3.1: Application層修正
ファイル: `backend/app/application/example_usecase.py`
- IExampleRepository をimport
- self.repository の型アノテーションを追加

### Task 4.1-4.3: 動作確認
- Dockerコンテナ起動
- curlまたはHTTPクライアントでAPIテスト
- レスポンスが正常であることを確認

## 注意事項
- 各フェーズは順番に実施する
- インポートエラーが発生した場合は、すぐに修正する
- 既存のコードロジックは変更しない（型定義とインターフェースのみ追加）

# 要求内容：ユニットテストのモック化実装

## 背景
前回の作業で完全な依存性注入（Constructor Injection）を実装し、Application層がDomain層のインターフェースのみに依存するようになった。これにより、**ユニットテストでモックリポジトリを注入可能**な構造が整った。

### 現在のテスト状況
- [test_examples.py](backend/tests/test_examples.py) - 統合テスト（API層のテスト）のみ存在
- Application層（`ExampleUseCase`）の**ユニットテストが存在しない**
- 既存テストはDB接続が必要（SQLiteを使用）

### 問題点
1. **ユニットテストがない**
   - ビジネスロジックを独立してテストできない
   - DB接続が必須で遅い
   - テストのセットアップが複雑

2. **モックの活用ができていない**
   - 前回の依存性注入の改善が活かされていない
   - `IExampleRepository` をモック化したテストが存在しない

## 要求事項

### 1. モックリポジトリの作成
- `IExampleRepository` を実装したモッククラスを作成
- テスト用のインメモリデータストアを持つ
- DB接続不要で動作

### 2. Application層のユニットテスト追加
- `ExampleUseCase` の各メソッドをテスト
  - `create_example` - サンプル作成ロジック
  - `get_example` - サンプル取得ロジック
  - `list_examples` - サンプル一覧取得ロジック
- モックリポジトリを使用してDB不要のテストを実現

### 3. テスト構造の整理
- ユニットテスト用のディレクトリ構造を作成
  - `tests/unit/` - ユニットテスト
  - `tests/integration/` - 統合テスト（既存）
- テストの目的を明確に分離

### 4. 既存の統合テストは維持
- [test_examples.py](backend/tests/test_examples.py) は統合テストとして維持
- API層全体の動作確認として機能

## 受け入れ条件

1. モックリポジトリクラス（`MockExampleRepository`）が存在する
2. Application層のユニットテストが存在する
3. ユニットテストがDB接続なしで実行できる
4. ユニットテストが高速に実行できる（< 1秒）
5. 既存の統合テストが引き続き動作する
6. テストディレクトリが `unit/` と `integration/` に分離されている

## 制約事項

1. 既存の統合テストの動作を変更しない
2. pytestのフレームワークを使用
3. 標準ライブラリまたはpytestのモック機能を使用（追加ライブラリ不要）
4. テストの実行コマンドは既存のまま（`pytest`）

## 影響範囲

### 新規作成ファイル
- `tests/unit/__init__.py`
- `tests/unit/test_example_usecase.py` - UseCaseのユニットテスト
- `tests/unit/mocks/__init__.py`
- `tests/unit/mocks/mock_example_repository.py` - モックリポジトリ

### 変更ファイル
- `tests/test_examples.py` → `tests/integration/test_examples.py` に移動
- `tests/test_health.py` → `tests/integration/test_health.py` に移動（オプション）

### 変更不要
- `tests/conftest.py` - 統合テスト用として維持
- Application層のコード - テストのみ追加

## 期待される効果

### 1. テストの高速化
```bash
# Before: 統合テストのみ（DB接続あり）
pytest tests/  # ~2-3秒

# After: ユニットテスト（DB接続なし）
pytest tests/unit/  # ~0.1-0.2秒
pytest tests/integration/  # ~2-3秒
```

### 2. テストの独立性向上
- ユニットテストはビジネスロジックのみに集中
- インフラの問題と分離してテスト可能

### 3. 開発体験の向上
- ビジネスロジック変更時のフィードバックが高速
- TDD（テスト駆動開発）がしやすくなる

## テストの種類と目的

### ユニットテスト（新規追加）
**目的：** ビジネスロジックの正確性を検証
**範囲：** Application層（`ExampleUseCase`）
**依存：** モックリポジトリ（DB不要）
**速度：** 高速（< 1秒）

### 統合テスト（既存）
**目的：** システム全体の動作を検証
**範囲：** API層 + Application層 + Infrastructure層
**依存：** 実際のDB（SQLite）
**速度：** 中速（2-3秒）

## 参考情報

### 関連する前回の作業
- [.steering/20250120-implement-constructor-injection/](./../20250120-implement-constructor-injection/) - 依存性注入の実装
- この改善により、モック注入が可能になった

### テストピラミッド
```
     /\
    /  \     E2E Tests (少数)
   /────\
  /      \   Integration Tests (中程度)
 /────────\
/          \  Unit Tests (多数・高速)
────────────
```

今回はこのピラミッドの基盤となるユニットテストを追加する。

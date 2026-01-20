# タスクリスト：ユニットテストのモック化実装

## タスクの進捗状況

### Phase 1: ディレクトリ構造とモック作成
- [ ] テストディレクトリ構造を作成
  - `tests/unit/` ディレクトリ作成
  - `tests/unit/domain/` ディレクトリ作成
  - `tests/unit/application/` ディレクトリ作成
  - `tests/unit/mocks/` ディレクトリ作成
  - `tests/integration/` ディレクトリ作成
- [ ] 各ディレクトリに `__init__.py` を作成
- [ ] モックリポジトリを作成
  - `tests/unit/mocks/mock_example_repository.py`
- [ ] 既存テストを移動
  - `tests/test_examples.py` → `tests/integration/test_examples.py`
  - `tests/test_health.py` → `tests/integration/test_health.py`
  - `tests/conftest.py` → `tests/integration/conftest.py` にコピー

### Phase 2: Domain層のユニットテスト作成
- [ ] `tests/unit/domain/test_example.py` を作成
  - エンティティ生成テスト
  - `update_name` 正常系テスト
  - `update_name` 異常系テスト（空文字）
  - `update_name` 異常系テスト（空白のみ）
  - フィールド保持のテスト

### Phase 3: Application層のユニットテスト作成
- [ ] `tests/unit/application/test_example_usecase.py` を作成
  - `create_example` 正常系テスト
  - `create_example` リポジトリ保存確認テスト
  - 複数作成テスト
  - `get_example` 正常系テスト
  - `get_example` 存在しないIDテスト
  - `list_examples` 空リストテスト
  - `list_examples` データありテスト
  - descriptionなし作成テスト

### Phase 4: 動作確認
- [ ] ユニットテストの実行確認
  - Domain層のテスト実行
  - Application層のテスト実行
  - 全ユニットテスト実行
- [ ] 統合テストの実行確認
  - 移動後の統合テストが正常動作することを確認
- [ ] 全テスト実行
  - ユニットテスト + 統合テストの両方

### Phase 5: 検証とクリーンアップ
- [ ] テストカバレッジの確認
- [ ] 実行速度の測定
- [ ] 不要ファイルの削除（元の `tests/test_*.py`）

## 完了条件

### 機能的完了条件
1. モックリポジトリが `IExampleRepository` を実装している
2. Domain層のユニットテストが存在し、パスする
3. Application層のユニットテストが存在し、パスする
4. ユニットテストがDB接続なしで実行できる
5. 既存の統合テストが引き続き動作する
6. テストディレクトリが `unit/` と `integration/` に分離されている

### 技術的完了条件
1. ユニットテストの実行速度が 1秒未満
2. 統合テストが既存通り動作（2-3秒程度）
3. 全テストがパスする
4. Pythonのインポートエラーが発生しない

## 各タスクの詳細

### Task 1.1: ディレクトリ構造作成

```bash
mkdir -p backend/tests/unit/domain
mkdir -p backend/tests/unit/application
mkdir -p backend/tests/unit/mocks
mkdir -p backend/tests/integration
```

### Task 1.2: __init__.py 作成

各ディレクトリに空の `__init__.py` を作成：
- `tests/unit/__init__.py`
- `tests/unit/domain/__init__.py`
- `tests/unit/application/__init__.py`
- `tests/unit/mocks/__init__.py`
- `tests/integration/__init__.py`

### Task 1.3: モックリポジトリ作成

ファイル: `tests/unit/mocks/mock_example_repository.py`

**実装内容：**
- `IExampleRepository` を継承
- インメモリデータストア（`dict`）
- `find_by_id`, `find_all`, `save` メソッド実装
- `clear()` ヘルパーメソッド

### Task 1.4: 既存テストの移動

```bash
# ファイル移動
mv backend/tests/test_examples.py backend/tests/integration/
mv backend/tests/test_health.py backend/tests/integration/

# conftest.pyをコピー（統合テスト用）
cp backend/tests/conftest.py backend/tests/integration/conftest.py
```

**注意：** 元の `tests/conftest.py` は後で削除するか、空にする

### Task 2.1: Domain層テスト作成

ファイル: `tests/unit/domain/test_example.py`

**テストケース：**
1. `test_create_example` - エンティティ生成
2. `test_update_name_success` - 名前更新の正常系
3. `test_update_name_with_empty_string_raises_error` - 空文字でエラー
4. `test_update_name_with_whitespace_only_raises_error` - 空白のみでエラー
5. `test_update_name_preserves_other_fields` - 他フィールド保持

### Task 3.1: Application層テスト作成

ファイル: `tests/unit/application/test_example_usecase.py`

**テストケース：**
1. `test_create_example_success` - サンプル作成の正常系
2. `test_create_example_saves_to_repository` - リポジトリ保存確認
3. `test_create_multiple_examples` - 複数作成
4. `test_get_example_success` - サンプル取得の正常系
5. `test_get_example_not_found` - 存在しないID
6. `test_list_examples_empty` - 空リスト
7. `test_list_examples_with_data` - データあり
8. `test_create_example_without_description` - descriptionなし

**setup_method：**
```python
def setup_method(self):
    self.mock_repo = MockExampleRepository()
    self.usecase = ExampleUseCase(self.mock_repo)
```

### Task 4.1-4.3: テスト実行確認

```bash
# ユニットテストのみ実行（Domain層）
pytest tests/unit/domain/ -v

# ユニットテストのみ実行（Application層）
pytest tests/unit/application/ -v

# 全ユニットテスト実行
pytest tests/unit/ -v

# 統合テスト実行
pytest tests/integration/ -v

# 全テスト実行
pytest -v
```

### Task 5.1: カバレッジ確認

```bash
pytest --cov=app --cov-report=term-missing tests/
```

### Task 5.2: 実行速度測定

```bash
# ユニットテストの速度
time pytest tests/unit/

# 統合テストの速度
time pytest tests/integration/

# 全体の速度
time pytest
```

### Task 5.3: クリーンアップ

不要になった元のファイルを削除：
```bash
# 移動済みファイルの削除（バックアップ確認後）
rm backend/tests/test_examples.py
rm backend/tests/test_health.py
```

`tests/conftest.py` を空にするか、ユニットテスト用に変更。

## 実装時の注意事項

### 1. インポートパスの確認
- モックは `tests.unit.mocks.mock_example_repository` からimport
- Application層は `app.application.example_usecase` からimport
- Domain層は `app.domain.example` からimport

### 2. テストの独立性
- 各テストメソッドは独立して実行可能
- `setup_method` でテストデータをリセット
- テスト間で状態を共有しない

### 3. pytestの規則
- テストファイル名は `test_*.py` または `*_test.py`
- テストクラス名は `Test*`
- テストメソッド名は `test_*`

### 4. 既存テストの互換性
- 統合テストは移動のみで内容は変更しない
- `conftest.py` のfixtureが引き続き動作することを確認

## 期待される結果

### テスト実行結果

**ユニットテスト（高速）：**
```bash
$ pytest tests/unit/ -v
======================== test session starts =========================
tests/unit/domain/test_example.py::TestExample::test_create_example PASSED
tests/unit/domain/test_example.py::TestExample::test_update_name_success PASSED
tests/unit/domain/test_example.py::TestExample::test_update_name_with_empty_string_raises_error PASSED
tests/unit/domain/test_example.py::TestExample::test_update_name_with_whitespace_only_raises_error PASSED
tests/unit/domain/test_example.py::TestExample::test_update_name_preserves_other_fields PASSED
tests/unit/application/test_example_usecase.py::TestExampleUseCase::test_create_example_success PASSED
tests/unit/application/test_example_usecase.py::TestExampleUseCase::test_create_example_saves_to_repository PASSED
tests/unit/application/test_example_usecase.py::TestExampleUseCase::test_create_multiple_examples PASSED
tests/unit/application/test_example_usecase.py::TestExampleUseCase::test_get_example_success PASSED
tests/unit/application/test_example_usecase.py::TestExampleUseCase::test_get_example_not_found PASSED
tests/unit/application/test_example_usecase.py::TestExampleUseCase::test_list_examples_empty PASSED
tests/unit/application/test_example_usecase.py::TestExampleUseCase::test_list_examples_with_data PASSED
tests/unit/application/test_example_usecase.py::TestExampleUseCase::test_create_example_without_description PASSED
======================== 13 passed in 0.12s ==========================
```

**統合テスト：**
```bash
$ pytest tests/integration/ -v
======================== test session starts =========================
tests/integration/test_examples.py::test_create_example PASSED
tests/integration/test_examples.py::test_get_example PASSED
tests/integration/test_examples.py::test_list_examples PASSED
tests/integration/test_health.py::test_health PASSED
======================== 4 passed in 2.45s ===========================
```

**全テスト：**
```bash
$ pytest -v
======================== 17 passed in 2.57s ==========================
```

## テストピラミッドの実現

```
        /\
       /  \      統合テスト: 4 tests (~2.5s)
      /    \
     /──────\
    /        \   Application層: 8 tests (~0.08s)
   /──────────\
  /            \ Domain層: 5 tests (~0.04s)
 /──────────────\
──────────────────
```

## 関連ドキュメント

- [requirements.md](./requirements.md) - 要求内容とテストの種類
- [design.md](./design.md) - 詳細設計とテストコード例
- [前回の作業](./../20250120-implement-constructor-injection/) - 依存性注入の実装

# 要求内容：完全な依存性注入（Constructor Injection）の実装

## 背景
前回の作業でDomain層にリポジトリインターフェースを追加したが、Application層で以下の問題が残っている：

**現在の実装（問題あり）：**
```python
class ExampleUseCase:
    def __init__(self, db: Session):
        self.repository: IExampleRepository = ExampleRepository(db)
```

**問題点：**
1. **ユニットテストができない**
   - `ExampleUseCase` のコンストラクタ内で `ExampleRepository` を直接インスタンス化
   - テスト時にモックリポジトリを注入できない
   - データベース接続なしでビジネスロジックのテストが不可能

2. **依存性注入が不完全**
   - インターフェースは定義したが、実際には具象クラスに依存
   - [example_usecase.py:7](backend/app/application/example_usecase.py#L7) で `ExampleRepository` をimport
   - [example_usecase.py:15](backend/app/application/example_usecase.py#L15) で具象クラスを直接生成

3. **レイヤー間の責務が不明確**
   - Application層がInfrastructure層の具象クラスを知っている
   - 本来はAPI層（またはDIコンテナ）が依存解決すべき

## 要求事項

### 1. Application層の完全な依存性注入化
- `ExampleUseCase` がリポジトリインターフェースのみに依存
- コンストラクタでリポジトリを受け取る（Constructor Injection）
- `ExampleRepository` への直接的な依存を削除

### 2. API層での依存解決
- エンドポイント（[examples.py](backend/app/api/v1/endpoints/examples.py)）で依存を解決
- `get_db()` を使って `Session` を取得
- `Session` から `ExampleRepository` をインスタンス化
- `ExampleRepository` を `ExampleUseCase` に注入

### 3. テスト容易性の確保
- ユニットテストでモックリポジトリを簡単に注入可能
- データベース接続なしでビジネスロジックをテスト可能

## 受け入れ条件

1. `ExampleUseCase` が `ExampleRepository` をimportしていない
2. `ExampleUseCase` のコンストラクタが `IExampleRepository` を受け取る
3. API層のエンドポイントで依存を解決している
4. 既存のAPIが正常に動作する
5. ユニットテストでモックリポジトリを注入できる構造になっている

## 制約事項

1. 既存のデータベーススキーマは変更しない
2. 既存のAPIエンドポイントの動作を変更しない
3. DIコンテナライブラリは導入しない（シンプルな手動DIで実装）
4. `get_db()` の仕組みは既存のまま維持

## 影響範囲

### 変更対象ファイル
- 修正：`app/application/example_usecase.py` - コンストラクタシグネチャ変更
- 修正：`app/api/v1/endpoints/examples.py` - 依存解決ロジック追加

### 変更不要
- `app/domain/repositories/example_repository.py` - インターフェース
- `app/infrastructure/repositories/example_repository.py` - 実装
- `app/core/database.py` - DB接続

### 永続的ドキュメントへの影響
- `docs/architecture.md` - 依存性注入パターンの説明を追加する可能性
- `.steering/20250120-add-domain-repository-interfaces/design.md` - 将来の改善案が実現された

## 期待される変更イメージ

### Application層（example_usecase.py）
```python
# Before
def __init__(self, db: Session):
    self.repository: IExampleRepository = ExampleRepository(db)

# After
def __init__(self, repository: IExampleRepository):
    self.repository = repository
```

### API層（examples.py）
```python
# Before
usecase = ExampleUseCase(db)

# After
repository = ExampleRepository(db)
usecase = ExampleUseCase(repository)
```

## テストの改善例

この変更により、以下のようなユニットテストが可能になる：

```python
# ユニットテストの例
class MockExampleRepository(IExampleRepository):
    def find_by_id(self, example_id: int) -> Example | None:
        return Example(id=1, name="Mock", ...)

    def find_all(self) -> list[Example]:
        return []

    def save(self, example: Example) -> Example:
        return example

# テストコード
def test_create_example():
    mock_repo = MockExampleRepository()
    usecase = ExampleUseCase(mock_repo)  # DB接続不要！

    result = usecase.create_example(ExampleCreate(name="Test"))
    assert result.name == "Test"
```

## 参考情報

### 関連する前回の作業
- [.steering/20250120-add-domain-repository-interfaces/](../.steering/20250120-add-domain-repository-interfaces/) - リポジトリインターフェース追加作業
- [design.md](../.steering/20250120-add-domain-repository-interfaces/design.md) の「将来的な改善案」セクションで言及していた内容を実現

### 現在の問題箇所
- [example_usecase.py:7](backend/app/application/example_usecase.py#L7) - Infrastructure層への直接import
- [example_usecase.py:14-15](backend/app/application/example_usecase.py#L14-L15) - 具象クラスの直接インスタンス化

# 要求内容：Domain層へのRepositoryインターフェース追加

## 背景
現在のバックエンド実装では、レイヤードアーキテクチャとDDDを採用しているが、リポジトリパターンの実装において以下の問題がある：

1. **依存関係の逆転が実現されていない**
   - `app/application/example_usecase.py:6` でapplication層がinfrastructure層の具象クラス `ExampleRepository` に直接依存している
   - domain層にリポジトリのインターフェースが存在しない

2. **DDDの原則違反**
   - domain層がインフラストラクチャの詳細から独立していない
   - テストやインフラ変更時の柔軟性が低い

## 要求事項

### 1. Domain層にRepositoryインターフェースを追加
- `app/domain/repositories/` ディレクトリを作成
- 抽象基底クラス（ABC）としてリポジトリインターフェースを定義
- ドメインモデルに対する永続化操作の契約を定義

### 2. Infrastructure層の実装クラスを修正
- 既存の `ExampleRepository` をインターフェースの実装として修正
- domain層のインターフェースを継承

### 3. Application層の依存関係を修正
- `ExampleUseCase` がdomain層のインターフェースに依存するよう修正
- 依存性注入（DI）により具象クラスを注入

### 4. 他のレイヤーへの影響を最小化
- API層（endpoints）への影響を確認・対応
- 既存の動作を維持

## 受け入れ条件

1. domain層に `IExampleRepository` インターフェース（ABCを使用）が存在する
2. infrastructure層の `ExampleRepository` が `IExampleRepository` を実装している
3. application層の `ExampleUseCase` が `IExampleRepository` に依存している
4. 既存のAPI動作が変更前と同じように動作する
5. 依存関係が以下の方向になっている：
   ```
   api → application → domain ← infrastructure
   ```
   （infrastructureがdomainに依存、applicationもdomainに依存）

## 制約事項

1. 既存のデータベーススキーマは変更しない
2. 既存のAPIエンドポイントの動作を変更しない
3. Pythonの標準的なABC（Abstract Base Class）パターンを使用する
4. 型ヒントを適切に使用し、mypyでの型チェックに対応する

## 影響範囲

### 変更対象ファイル
- 新規作成：`app/domain/repositories/__init__.py`
- 新規作成：`app/domain/repositories/example_repository.py`（インターフェース）
- 修正：`app/infrastructure/repositories/example_repository.py`
- 修正：`app/application/example_usecase.py`
- 確認：`app/api/v1/endpoints/` 配下のファイル

### 永続的ドキュメントへの影響
- `docs/architecture.md` - レイヤードアーキテクチャの説明を更新する必要がある可能性
- `docs/repository-structure.md` - リポジトリ構造の更新が必要

## 参考情報

### 現在の問題箇所
- [example_usecase.py:6](backend/app/application/example_usecase.py#L6) - infrastructure層への直接依存
- [example_usecase.py:14](backend/app/application/example_usecase.py#L14) - 具象クラスの直接インスタンス化

### 関連ファイル
- [example.py](backend/app/domain/example.py) - ドメインエンティティ
- [example_repository.py](backend/app/infrastructure/repositories/example_repository.py) - 現在の具象リポジトリ

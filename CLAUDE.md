# CLAUDE.md

## 概要
開発を進める上で遵守すべき標準ルールを定義します。

## プロジェクト構造
本リポジトリは、Amazon ECSを使用したWebアプリケーションを開発するためのテンプレートとなるリポジトリです。
以下に関するコードを取り扱います。
- AWS CDKによるIaC
- Dockerやdocker-compose, DevContainerを用いたローカル開発環境のコード
- FastAPIを用いたバックエンドアプリケーションのサンプルコード（レイヤードアーキテクチャ）
- Next.jsを用いたフロントエンドアプリケーションのサンプルコード



- **/architecture** - 技術仕様書
docs/architecture/ 以下に、下記のドキュメント群を作成してください。

  - AWSシステム構成設計書 - aws_infra.md
  - AWS環境構築設計書 - aws_construct.md
  - ローカル開発環境設計書 - local_dev.md
  - 開発ツールと手法 - tools.md
  - パフォーマンス要件 - performance.md

- **repository-structure.md** - リポジトリ構造定義書
  - フォルダ・ファイル構成
  - ディレクトリの役割
  - ファイル配置ルール

#### 2. 作業単位のドキュメント（`.steering/[YYYYMMDD]-[開発タイトル]/`）
特定の開発作業における「**今回何をするか**」を定義する一時的なステアリングファイル。

作業完了後は参照用として保持されますが、新しい作業では新しいディレクトリを作成します。
- **requirements.md** - 今回の作業の要求内容
  - 変更・追加する機能の説明
  - 受け入れ条件
  - 制約事項

- **design.md** - 変更内容の設計
  - 実装アプローチ
  - 変更するコンポーネント
  - データ構造の変更
  - 影響範囲の分析

- **tasklist.md** - タスクリスト
  - 具体的な実装タスク
  - タスクの進捗状況
  - 完了条件



### ステアリングディレクトリの命名規則
```
.steering/[YYYYMMDD]-[開発タイトル]/
```
**例：**
- `.steering/20250103-initial-implementation/`
- `.steering/20250115-add-tag-feature/`
- `.steering/20250120-fix-filter-bug/`
- `.steering/20250201-improve-performance/`


## 開発プロセス
### 初回セットアップ時の手順
#### 1. フォルダ作成
```bash
mkdir -p docs
mkdir -p .steering
```
#### 2. 永続的ドキュメント作成（`docs/`）

アプリケーション全体の設計を定義します。
各ドキュメントを作成後、必ず確認・承認を得てから次に進みます。
1. `docs/architecture.md` - 技術仕様書
2. `docs/repository-structure.md` - リポジトリ構造定義書



#### 3. 初回実装用のステアリングファイル作成
初回実装用のディレクトリを作成し、実装に必要なドキュメントを配置します。
```bash
mkdir -p .steering/[YYYYMMDD]-initial-implementation
```
作成するドキュメント：
1. `.steering/[YYYYMMDD]-initial-implementation/requirements.md` - 初回実装の要求
2. `.steering/[YYYYMMDD]-initial-implementation/design.md` - 実装設計
3. `.steering/[YYYYMMDD]-initial-implementation/tasklist.md` - 実装タスク


#### 4. 環境セットアップ

#### 5. 実装開始
`.steering/[YYYYMMDD]-initial-implementation/tasklist.md` に基づいて実装を進めます。


#### 6. 品質チェック


### 機能追加・修正時の手順
#### 1. 影響分析
- 永続的ドキュメント（`docs/`）への影響を確認
- 変更が基本設計に影響する場合は `docs/` を更新
#### 2. ステアリングディレクトリ作成
新しい作業用のディレクトリを作成します。
```bash
mkdir -p .steering/[YYYYMMDD]-[開発タイトル]
```
**例：**
```bash
mkdir -p .steering/20250115-add-tag-feature
```



#### 3. 作業ドキュメント作成
作業単位のドキュメントを作成します。
各ドキュメント作成後、必ず確認・承認を得てから次に進みます。

1. `.steering/[YYYYMMDD]-[開発タイトル]/requirements.md` - 要求内容
2. `.steering/[YYYYMMDD]-[開発タイトル]/design.md` - 設計
3. `.steering/[YYYYMMDD]-[開発タイトル]/tasklist.md` - タスクリスト
**重要：** 1ファイルごとに作成後、必ず確認・承認を得てから次のファイル作成を行う


#### 4. 永続的ドキュメント更新（必要な場合のみ）
変更が基本設計に影響する場合、該当する `docs/` 内のドキュメントを更新します。


#### 5. 実装開始

`.steering/[YYYYMMDD]-[開発タイトル]/tasklist.md` に基づいて実装を進めます。

#### 6. 品質チェック


## ドキュメント管理の原則
### 永続的ドキュメント（`docs/`）
- アプリケーションの基本設計を記述
- 頻繁に更新されない
- 大きな設計変更時のみ更新
- プロジェクト全体の「北極星」として機能
### 作業単位のドキュメント（`.steering/`）
- 特定の作業・変更に特化
- 作業ごとに新しいディレクトリを作成
- 作業完了後は履歴として保持
- 変更の意図と経緯を記録



## 注意事項
- ドキュメントの作成・更新は段階的に行い、各段階で承認を得る
- `.steering/` のディレクトリ名は日付と開発タイトルで明確に識別できるようにする
- 永続的ドキュメントと作業単位のドキュメントを混同しない
- 図表は必要最小限に留め、メンテナンスコストを抑える
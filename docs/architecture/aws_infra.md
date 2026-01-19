# AWSシステム構成設計書

## 概要
本ドキュメントは、Amazon ECSを使用したWebアプリケーションのAWSインフラストラクチャ設計を定義します。
フロントエンドはAWS Amplify、バックエンドはECS Fargateで構成されます。

## システムアーキテクチャ

### 全体構成
マルチAZ構成によるHighly Available（高可用性）なWebアプリケーション基盤を構築します。

```
Client → Route53 → Amplify (Frontend)
                → MAF → Orchestrator → ECS (Fargate) → Aurora
```

## フロントエンド構成

### AWS Amplify
- **用途**: Next.jsアプリケーションのホスティング
- **デプロイ**: GitHubリポジトリと連携した自動デプロイ
- **配信**: Amplifyの組み込みCDN
- **HTTPS**: 自動SSL証明書管理
- **環境**: 開発環境と本番環境の分離

## ネットワーク構成

### VPC設計
- **リージョン**: ap-northeast-1 (東京)
- **Availability Zones**: 2つのAZ（AZ-1, AZ-2）を使用

### サブネット設計

#### パブリックサブネット
- **AZ-1 Public Subnet**
- **AZ-2 Public Subnet**
- **用途**:
  - インターネットゲートウェイへのルーティング
  - 外部アクセス可能なリソースの配置

#### プライベートサブネット
- **AZ-1 Private Subnet**
- **AZ-2 Private Subnet**
- **用途**:
  - ECS Fargateタスクの実行
  - Aurora（データベース）の配置
  - 外部へのアクセスはNAT Gateway経由

## コンピューティング

### Amazon ECS (Fargate)
#### クラスタ構成
- **起動タイプ**: Fargate (サーバーレスコンテナ)
- **デプロイ戦略**: ローリングアップデート
- **Auto Scaling**: CPU/メモリ使用率ベース

#### サービス設計
- **バックエンド（FastAPI）サービス**
  - タスク数: マルチAZ構成
  - プライベートサブネットに配置
  - Auroraデータベースへのアクセス

#### コンテナ設計
- **ECR (Elastic Container Registry)**
  - バックエンド用イメージリポジトリ
  - イメージスキャン: 有効
  - Service/Task Archiveからのイメージ管理

## オーケストレーション

### Orchestrator
- **用途**: ECSタスクの起動制御とワークフロー管理
- **構成要素**:
  - Auto scaling: 自動スケーリング制御
  - Service: ECSサービス管理
  - Task Archive: タスク定義の履歴管理
  - Container (Fargate): 実行環境

## イベント駆動アーキテクチャ

### Amazon EventBridge
- **用途**: イベントルーティングとスケジューリング
- **連携**: Step Functionsとのイベント連携

### AWS Step Functions
- **用途**: ワークフローの制御とオーケストレーション
- **ユースケース**:
  - バッチ処理の制御
  - マルチステップのビジネスロジック実行

## データベース

### Amazon Aurora (PostgreSQL互換)
- **構成**: プライマリ + レプリカ
- **デプロイ**: マルチAZ（AZ-1とAZ-2）
  - Aurora Primary: AZ-1のプライベートサブネット
  - Aurora Replica: AZ-2のプライベートサブネット
- **接続**: プライベートサブネット内からのみアクセス可能
- **暗号化**: KMS による保存時暗号化を有効化
- **バックアップ**: 自動バックアップとスナップショット

### Private Endpoints
- **構成**: マルチAZ構成によるプライベートエンドポイント
- **用途**: VPC内からのセキュアなアクセス

## CI/CD

### ソースコード管理
- **GitHub**: ソースコードリポジトリ

### CI/CDパイプライン
#### フロントエンド
- **GitHub** → **AWS Amplify**
  - Gitプッシュ時の自動ビルド・デプロイ

#### バックエンド
- **GitHub** → **GitHub Actions** → **ECR** → **ECS**
  1. コードチェックアウト
  2. Dockerイメージビルド
  3. ECRへプッシュ
  4. ECSタスク定義更新
  5. ECSサービス更新

## セキュリティ・ガバナンス

### セキュリティサービス

#### GuardDuty
- **用途**: 脅威検出とセキュリティモニタリング
- **範囲**: AWSアカウント全体の不正アクセス検出

#### AWS Config
- **用途**: リソース構成の記録と監査
- **コンプライアンス**: 設定変更の追跡とルール遵守確認

#### Amazon Macie
- **用途**: S3データのセキュリティとプライバシー保護
- **機能**: 機密データの検出と分類

### WAF (Web Application Firewall)
- **MAF**: Web Application Firewall (MAFと表記)
- **用途**: Webアプリケーションの保護
- **配置**: Amplify/オーケストレーター層への接続制御

## DNS

### Amazon Route 53
- **用途**: DNSホスティングとルーティング
- **レコード管理**:
  - フロントエンド: Amplifyへのルーティング
  - バックエンド: VPC内のプライベートDNS

## 監視とロギング

### Amazon CloudWatch Logs
- **ログ収集元**:
  - ECSコンテナログ
  - Amplifyアプリケーションログ
  - Step Functionsワークフローログ
- **ログ保持期間**: 環境に応じて設定

### CloudWatch (Logs)
- **Observability**: 可観測性の統合管理
- **連携**: S3へのログアーカイブ

## ストレージ

### Amazon S3
- **用途**:
  - ログアーカイブ（CloudWatch Logs連携）
  - バックアップデータ保存
  - 静的ファイルストレージ（必要に応じて）

## デプロイ戦略

### フロントエンド (Amplify)
- **デプロイ**: GitHubプッシュ時の自動デプロイ
- **環境分離**: ブランチベースの環境管理

### バックエンド (ECS)
- **デプロイ**: GitHub Actions経由のCI/CDパイプライン
- **方式**: ローリングアップデート
- **ロールバック**: 以前のタスク定義への切り替え

## スケーラビリティ

### Auto Scaling
- **ECS Auto Scaling**: CPU/メモリ使用率ベース
- **Aurora Auto Scaling**: リードレプリカの自動追加

### マルチAZ構成
- すべての主要コンポーネントがAZ-1とAZ-2に冗長配置
- 可用性とフェイルオーバーの確保

## AWS CDKによるIaC管理

### スタック構成
すべてのインフラストラクチャをAWS CDKでコード管理

推奨スタック分割:
- **ネットワークスタック**: VPC、サブネット
- **データベーススタック**: Aurora
- **コンピューティングスタック**: ECS、Fargate
- **フロントエンドスタック**: Amplify
- **セキュリティスタック**: GuardDuty、Config、WAF
- **オーケストレーションスタック**: Step Functions、EventBridge

## 更新履歴
- 2026-01-19: 初版作成

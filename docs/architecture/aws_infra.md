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
- **用途**: Next.jsアプリケーションのホスティング（将来的に実装予定）
- **デプロイ**: GitHubリポジトリと連携した自動デプロイ
- **配信**: Amplifyの組み込みCDN
- **HTTPS**: 自動SSL証明書管理
- **環境**: 開発環境と本番環境の分離
- **注意**: 初期構築フェーズでは実装せず、バックエンド基盤構築後に追加予定

## ネットワーク構成

### VPC設計
- **リージョン**: ap-northeast-1 (東京)
- **Availability Zones**: 2つのAZ（AZ-1, AZ-2）を使用
- **インターネット接続**: パブリックサブネットはインターネットゲートウェイ経由、プライベートサブネットはVPCエンドポイント経由でAWSサービスにアクセス

### VPCエンドポイント（コスト最適化）
NAT Gatewayの代わりにVPCエンドポイントを使用し、コストを削減します（月額約$35の節約）。

#### Gateway型エンドポイント（無料）
- **S3**: ログ保存、静的ファイルアクセス用

#### Interface型エンドポイント（有料: 約$7.2/月/個）
- **ECR API**: ECRリポジトリへのAPI呼び出し用
- **ECR DKR**: Dockerイメージのプル用
- **Secrets Manager**: データベース認証情報の取得用
- **CloudWatch Logs**: ログ出力用

**コスト比較**:
- NAT Gateway方式: 約$64/月（2個 × $32） + データ転送料
- VPCエンドポイント方式: 約$28.8/月（Interface型 × 4個） + $0（Gateway型）
- **削減額**: 約$35/月（年間約$420）

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
  - 外部へのアクセスはVPCエンドポイント経由（AWSサービスのみ）

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
  - イメージスキャン: プッシュ時の自動スキャン有効
  - ライフサイクルポリシー: 最新10イメージを保持、それ以外は自動削除
  - Service/Task Archiveからのイメージ管理

### Application Load Balancer (ALB)
- **配置**: パブリックサブネット（マルチAZ）
- **リスナー**:
  - HTTPS (443): ACM証明書によるSSL/TLS終端
  - HTTP (80): HTTPSへのリダイレクト
- **ターゲットグループ**: ECS Fargateタスク（プライベートサブネット）
- **ヘルスチェック**: /healthエンドポイント
- **アクセスログ**: S3バケットへの保存
- **WAF統合**: Web Application Firewallの関連付け
- **カスタムドメイン**: Route 53との連携（api.example.com）

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
- **構成**: プライマリ + レプリカ（プロビジョニング型）
- **デプロイ**: マルチAZ（AZ-1とAZ-2）
  - Aurora Primary: AZ-1のプライベートサブネット
  - Aurora Replica: AZ-2のプライベートサブネット
- **インスタンスクラス**: db.t4g.medium（開発環境）、db.r6g.large（本番環境）
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
- **ログ収集対象**: ERRORレベル以上のログのみ（コスト最適化）
- **ログ収集元**:
  - ECSコンテナログ（Fluent Bit経由、ERRORレベル以上）
  - Step Functionsワークフローログ
  - VPCフローログ
- **ログ保持期間**:
  - 開発環境: 7日
  - 本番環境: 30日
- **用途**: エラー検知、アラート、即座のトラブルシューティング

### Fluent Bit
- **配置**: ECSタスク内のサイドカーコンテナとして実行
- **役割**: ログのフィルタリングと振り分け
- **機能**:
  - アプリケーションログのJSON形式への変換（必要に応じて）
  - ログレベルによる振り分け
    - ERRORレベル以上 → CloudWatch Logs
    - 全ログ → S3バケット
- **リソース**: CPU 50m、Memory 128Mi（軽量設定）

### CloudWatch Container Insights
- **用途**: ECSクラスタ・サービス・タスクのメトリクス自動収集
- **収集メトリクス**:
  - CPU、メモリ使用率
  - ネットワーク送受信量
  - タスク数、起動失敗数
- **ダッシュボード**: 自動生成されるパフォーマンスダッシュボード

### CloudWatch Alarms
- **監視対象**:
  - ECSタスクのエラーログ検出（ERRORレベル以上）
  - ECSサービスのCPU/メモリ使用率
  - Auroraのディスク使用率、接続数
  - ALBの5xxエラー率
- **通知**: SNSトピック経由でメール通知

### CloudWatch Dashboards
- **用途**: システム全体の監視ダッシュボード
- **カスタムダッシュボード**: ECS、Aurora、ALBメトリクスの統合表示
- **Container Insights**: ECS専用の自動生成ダッシュボード

### Amazon Athena（オプション）
- **用途**: S3に保存されたログのクエリと分析
- **連携**: AWS Glue Data Catalogでテーブル定義
- **クエリ例**:
  - 特定期間のアクセスパターン分析
  - パフォーマンス分析
  - ユーザー行動分析

## ストレージ

### Amazon S3
- **用途**:
  - 全レベルログの長期保存（Fluent Bit経由、コスト最適化）
  - CloudWatch Logsからのログアーカイブ（オプション）
  - バックアップデータ保存
  - 静的ファイルストレージ（必要に応じて）
- **ログバケット構成**:
  - 保存形式: Gzip圧縮、パーティション構成（year/month/day/hour）
  - ライフサイクルポリシー:
    - 90日後: Glacier Flexible Retrievalへ移行
    - 1年後: 削除（コンプライアンス要件に応じて調整）
  - 暗号化: SSE-S3
  - バージョニング: 有効
  - パブリックアクセスブロック: 有効

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
- **コンピューティングスタック**: ECS、Fargate、ECR、Fluent Bit
- **フロントエンドスタック**: Amplify（将来実装）
- **セキュリティスタック**: GuardDuty、Config、WAF
- **モニタリングスタック**: CloudWatch Logs、CloudWatch Alarms、SNS、S3（ログアーカイブ）
- **オーケストレーションスタック**: Step Functions、EventBridge（将来実装）

## アラート・通知

### Amazon SNS
- **用途**: CloudWatch Alarmsからの通知受信
- **通知先**: メール、Slack（オプション）
- **トピック構成**:
  - critical-alerts: 本番環境のクリティカルアラート
  - warning-alerts: 警告レベルのアラート

## 更新履歴
- 2026-01-22: NAT GatewayをVPCエンドポイントに変更（コスト最適化）
- 2026-01-21: Fluent Bit、CloudWatch Alarms、SNS、ECRライフサイクル設定追加、Aurora構成変更、Amplifyを将来実装に変更
- 2026-01-19: 初版作成

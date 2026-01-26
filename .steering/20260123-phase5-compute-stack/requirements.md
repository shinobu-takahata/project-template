# フェーズ5: コンピューティング基盤 - 要求仕様書

## 概要
AWS CDK実装計画書のフェーズ5として、コンピューティング基盤を構築する。
ECSクラスター、ECRリポジトリ、ALB、Fargateサービスを含む。

## 参照ドキュメント
- [implements_aws_by_cdk_plan.md](../../docs/architecture/implements_aws_by_cdk_plan.md) - セクション5.1〜5.4

## 要求事項

### 5.1 ECRリポジトリの作成
- バックエンドAPI用ECRリポジトリ
- イメージスキャン: プッシュ時の自動スキャン有効
- イメージタグの変更可能性: MUTABLE
- ライフサイクルポリシー: 最新10イメージを保持、それ以外は自動削除
- 暗号化: AES-256

### 5.2 Application Load Balancerの構築
- ALBの作成（インターネット向け）
- パブリックサブネット（マルチAZ）への配置
- セキュリティグループ:
  - インバウンド: HTTPS (443)、HTTP (80) from 0.0.0.0/0
  - アウトバウンド: ECSセキュリティグループへ
- ターゲットグループの作成:
  - ターゲットタイプ: IP（Fargate用）
  - プロトコル: HTTP (ポート8000)
  - ヘルスチェック: /health、間隔30秒、タイムアウト5秒
- **HTTPリスナー（ポート80）**: 初期段階ではHTTPのみで動作
- **HTTPS対応はオプション**: 証明書が準備でき次第、HTTPSリスナーを追加
- アクセスログのS3保存
- WAFの関連付け（SecurityStackで作成したWeb ACL）
- **Route 53はスキップ**: Hosted Zoneが存在しないため、DNS設定は後日対応

### 5.3 ECS Clusterの作成
- ECS Clusterの作成
- Container Insightsの有効化

### 5.4 ECS Fargate Service（FastAPI + Fluent Bit）の実装
- ECSタスク定義の作成:
  - Fargate起動タイプ
  - CPU、メモリ: 環境設定から取得
  - メインコンテナ（FastAPI）: ECRイメージ参照、ポート8000公開、FireLens経由でログ出力
  - サイドカーコンテナ（Fluent Bit）: FireLens設定
- ECSサービスの作成:
  - プライベートサブネットへの配置
  - 希望タスク数: 2（マルチAZ構成）
  - デプロイ設定: ローリングアップデート
- セキュリティグループ:
  - インバウンド: ALBからのアクセス（ポート8000）
  - アウトバウンド: Auroraへの接続（ポート5432）、HTTPS（443）
- タスク実行ロール: ECRイメージプル、Secrets Manager読み取り、CloudWatch Logs書き込み
- タスクロール: S3書き込み（ログバケット）
- Service Auto Scaling: CPU使用率ベース（70%でスケール）、最小2、最大10

## 依存関係
- NetworkStack: VPC、サブネット
- SecurityStack: WAF Web ACL ARN
- DatabaseStack: Aurora接続情報（Secrets Manager ARN）

## 受け入れ条件
1. ECRリポジトリが作成され、イメージスキャンとライフサイクルポリシーが有効
2. ALBがパブリックサブネットに配置され、HTTPリスナーが設定されている
3. ECSクラスターがContainer Insights有効で作成されている
4. ECS Fargateサービスがプライベートサブネットで起動可能
5. Fluent Bitサイドカーが設定されている
6. Auto Scalingが設定されている
7. `cdk synth`が正常に完了する
8. TypeScriptのコンパイルエラーがない

## 制約事項
- **ACM証明書はまだ存在しない**: 初期段階ではHTTPのみで動作。HTTPS対応は後日追加
- **Hosted Zoneは存在しない**: Route 53のDNS設定は後日対応
- 初回デプロイ時はECRにイメージがないため、ECSサービスは起動失敗する可能性あり

## 将来対応（HTTPS/DNS）
1. ドメインを取得してRoute 53にHosted Zoneを作成
2. ACM証明書を作成（DNS検証）
3. ALBにHTTPSリスナーを追加
4. HTTP → HTTPSリダイレクトを設定
5. Route 53 AレコードでALBを指定

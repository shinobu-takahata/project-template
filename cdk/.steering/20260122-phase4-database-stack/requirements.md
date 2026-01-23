# フェーズ4: データベース基盤 - 要求定義書

## 概要
DatabaseStackを実装し、Aurora PostgreSQL Clusterとその関連リソースを構築します。
プライマリ・レプリカ構成によるマルチAZ高可用性データベース基盤を提供します。

## 目的
- Aurora PostgreSQL Clusterの実装（プロビジョニング型）
- マルチAZ構成による高可用性の実現
- セキュアなデータベース接続の確保（Secrets Manager統合）
- 環境別の適切な設定（開発環境と本番環境）
- パフォーマンス監視基盤の構築（Performance Insights）

## 実装範囲

### 1. Aurora PostgreSQL Cluster
#### 構成
- **エンジン**: Aurora PostgreSQL互換（プロビジョニング型）
- **クラスタ構成**: プライマリ + レプリカ
- **配置**: マルチAZ（ap-northeast-1a、ap-northeast-1c）
  - Primary Instance: AZ-1のプライベートサブネット
  - Replica Instance: AZ-2のプライベートサブネット

#### インスタンスクラス
- **開発環境（dev）**: db.t4g.small（コスト最適化）
- **本番環境（prod）**: db.r6g.large

#### セキュリティ設定
- **暗号化**: 保存時暗号化を有効化（KMS）
- **削除保護**:
  - 開発環境: 無効（false）
  - 本番環境: 有効（true）

#### バックアップ設定
- **バックアップ保持期間**:
  - 開発環境: 7日間
  - 本番環境: 30日間
- **バックアップウィンドウ**: 自動設定（推奨時間帯）
- **メンテナンスウィンドウ**: 自動設定（推奨時間帯）
- **スナップショット**: 削除時のスナップショット作成
  - 開発環境: スナップショット不要（DESTROY）
  - 本番環境: 削除前にスナップショット作成（SNAPSHOT）

### 2. DBサブネットグループ
- NetworkStackから取得したプライベートサブネットを使用
- マルチAZ構成のサブネットを含める
- 命名規則: `db-subnet-group-${envName}`

### 3. セキュリティグループ
- **DBセキュリティグループ**
  - PostgreSQLポート（5432）へのインバウンドルール
  - 送信元: ECSセキュリティグループからのアクセスのみ許可
  - アウトバウンド: すべて許可
  - 命名規則: `db-sg-${envName}`

### 4. Secrets Manager統合
- **シークレット管理**
  - データベース認証情報の自動生成
  - ユーザー名: `dbadmin`
  - パスワード: 自動生成（32文字、記号を含む）
  - シークレット名: `${envName}/aurora/credentials`
- **自動ローテーション**: 将来的な実装を検討（初期実装では無効）
- **削除ポリシー**:
  - 開発環境: 即座に削除可能
  - 本番環境: 7日間の回復期間を設定

### 5. Performance Insights
- **開発環境（dev）**: 無効
- **本番環境（prod）**: 有効
  - 保持期間: 7日間（無料枠）
  - パフォーマンスデータの収集と可視化

### 6. CloudWatch Logsエクスポート
以下のログをCloudWatch Logsにエクスポート：
- PostgreSQLログ
- アップグレードログ

### 7. エクスポート
以下の値を他のStackから参照できるようにエクスポート：
- **DBクラスタARN**: `${envName}-DbClusterArn`
- **DBクラスタエンドポイント**: `${envName}-DbClusterEndpoint`
- **DBクラスタリードエンドポイント**: `${envName}-DbClusterReadEndpoint`
- **DBシークレットARN**: `${envName}-DbSecretArn`
- **DBセキュリティグループID**: `${envName}-DbSecurityGroupId`

## 依存関係

### 前提条件
- フェーズ2（NetworkStack）が完了していること
  - VPC、プライベートサブネットが作成済み
- 環境設定ファイル（EnvConfig）が正しく設定されていること

### インポートする値
- **NetworkStack**から:
  - VPC ID: `${envName}-VpcId`
  - プライベートサブネットID（複数）: `${envName}-PrivateSubnetIds`
  - ECSセキュリティグループID: `${envName}-EcsSecurityGroupId`（フェーズ5で作成予定のため、現時点では参照しない）

### エクスポートする値（他Stackで使用）
- DBクラスタエンドポイント → ECSStackで使用
- DBシークレットARN → ECSStackで使用
- DBセキュリティグループID → ECSStackで使用

## 環境別設定

### 開発環境（dev）
- インスタンスクラス: `db.t4g.small`（コスト最適化）
- バックアップ保持: 7日間
- 削除保護: 無効
- Performance Insights: 無効
- 削除ポリシー: `DESTROY`（完全削除）

### 本番環境（prod）
- インスタンスクラス: `db.r6g.large`
- バックアップ保持: 30日間
- 削除保護: 有効
- Performance Insights: 有効（7日間保持）
- 削除ポリシー: `SNAPSHOT`（スナップショット作成後削除）

## 技術要件

### CDKリソース
- `@aws-cdk-lib/aws-rds` - Aurora Clusterの構築
- `@aws-cdk-lib/aws-ec2` - セキュリティグループ、サブネットグループ
- `@aws-cdk-lib/aws-secretsmanager` - データベース認証情報管理
- `@aws-cdk-lib/aws-kms` - 暗号化キー管理

### TypeScript
- 厳密な型定義
- 環境設定の型安全性
- null/undefined チェック

## 非機能要件

### セキュリティ
- データベース認証情報はSecrets Managerで管理
- プライベートサブネットにのみ配置
- ECSタスクからのアクセスのみ許可
- 保存時暗号化（KMS）を有効化
- 転送時暗号化（SSL/TLS）を有効化

### 可用性
- マルチAZ構成によるフェイルオーバー
- 自動バックアップによるデータ保護
- レプリカによる読み取りスケーラビリティ

### 運用性
- CloudWatch Logsへのログエクスポート
- Performance Insights（本番環境のみ）
- 自動メンテナンスウィンドウ
- 環境別の削除ポリシー

### コスト最適化
- 開発環境は小さいインスタンスクラス（t4g.medium）
- 開発環境はPerformance Insightsを無効化
- バックアップ保持期間を環境別に設定

## 制約事項

### 初期実装での非実装事項
以下の機能は初期実装では含めず、将来的な拡張として検討します：
- Secrets Managerの自動ローテーション
- データベースプロキシ（RDS Proxy）の導入
- 拡張モニタリング（Enhanced Monitoring）
- クロスリージョンレプリケーション
- IAM データベース認証

### 技術的制約
- **ECSセキュリティグループの参照**:
  - フェーズ5（ECSStack）でECSセキュリティグループが作成される
  - 現時点ではECSセキュリティグループへの参照は保留
  - DBセキュリティグループのインバウンドルールは後で追加（フェーズ5で実装）
  - 当面はDBセキュリティグループのみ作成し、ルールは最小限に留める

### 環境制約
- リージョン: ap-northeast-1（東京）のみサポート
- AZ: ap-northeast-1a、ap-northeast-1c の2つのみ使用

## 受け入れ基準

### 必須条件
- [ ] DatabaseStackが正しく実装されている
- [ ] Aurora PostgreSQL Clusterが作成されている（プライマリ + レプリカ）
- [ ] マルチAZ構成でデプロイされている
- [ ] Secrets Managerでデータベース認証情報が管理されている
- [ ] DBサブネットグループが正しく構成されている
- [ ] DBセキュリティグループが作成されている
- [ ] KMSによる保存時暗号化が有効化されている
- [ ] 環境別の設定が正しく適用されている（インスタンスクラス、バックアップ、削除保護）
- [ ] CloudWatch Logsへのログエクスポートが有効化されている
- [ ] 本番環境でPerformance Insightsが有効化されている
- [ ] 開発環境と本番環境でのCDK合成が成功する
- [ ] 開発環境へのデプロイが成功する

### 品質基準
- [ ] TypeScriptのコンパイルエラーがない
- [ ] 型安全性が保たれている
- [ ] 環境設定が適切に使用されている
- [ ] コードが読みやすく保守しやすい
- [ ] 適切なタグ付けがされている（Environment, Project, ManagedBy）

### ドキュメント
- [ ] コード内のコメントが適切に記述されている
- [ ] 複雑なロジックには説明コメントがある

## 次のステップ
フェーズ4完了後、フェーズ5（ECSStack）に進みます。
フェーズ5では以下を実装します：
- ECS Cluster
- ECS Task Definition
- ECS Service
- Application Load Balancer
- Target Group
- ECSセキュリティグループ
- DBセキュリティグループへのインバウンドルール追加

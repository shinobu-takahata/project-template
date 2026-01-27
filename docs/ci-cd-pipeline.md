# GitHub Actions CI/CD パイプライン

このプロジェクトでは、GitHub ActionsとAWS OIDC認証を使用して、ECSへの自動デプロイを実現しています。

## 📋 概要

### デプロイフロー

```
┌──────────────────┐
│   Git Push       │
│  (main/develop)  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ GitHub Actions   │
│   Triggered      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  OIDC Auth       │
│  with AWS        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Build Docker    │
│    Image         │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Push to ECR     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Update ECS Task  │
│   Definition     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Deploy to ECS   │
└──────────────────┘
```

## 🚀 クイックスタート

### 1. 前提条件の確認

- CDKスタックがデプロイ済みであること
- AWS CLIが設定済みであること
- Dockerがインストールされていること

### 2. セットアップスクリプトの実行

```bash
# GitHub Actions設定の確認と準備
./scripts/setup-github-actions.sh
```

このスクリプトは以下を実行します：
- AWS アカウントIDの取得
- CDKスタックの出力値確認
- GitHub Secrets設定のガイド表示
- (オプション) GitHub CLI経由での自動設定

### 3. GitHub Secretsの設定

GitHubリポジトリに必要なSecretを設定：

```bash
# GitHub CLIを使用する場合
gh secret set AWS_ACCOUNT_ID -b "YOUR_ACCOUNT_ID"

# または、GitHubのWebインターフェースで
# Settings > Secrets and variables > Actions > New repository secret
```

### 4. 初回イメージのプッシュ（推奨）

CDKデプロイ前に、まずイメージをECRにプッシュ：

```bash
# 初回イメージのビルドとプッシュ
./scripts/initial-push.sh
```

環境を選択（dev/prod）すると、イメージをビルドしてECRにプッシュします。

> **💡 推奨理由**: 先にイメージをプッシュしておくことで、CDKデプロイ時にECSタスクがすぐに起動できます。

### 5. ECS設定の更新

CDK設定でECSの`desiredCount`を更新：

```typescript
// cdk/lib/config/dev.ts
ecs: {
  desiredCount: 2,  // 0 → 2に変更
  minCapacity: 2,   // 0 → 2に変更
  maxCapacity: 10
}
```

### 6. CDKスタックのデプロイ

イメージが準備できたので、CDKをデプロイ：

```bash
cd cdk
npx cdk deploy --all
```

ECSサービスがすぐにタスクを起動し、アプリケーションが利用可能になります。

### 7. 自動デプロイの完了

以降、`main`または`develop`ブランチへのプッシュで、ECSサービスが自動的に更新されます：

```bash
git add .
git commit -m "feat: add new feature"
git push origin develop  # dev環境にデプロイ
```

> **💡 補足**: 初回以降は、GitHub Actionsが自動的にビルド＆デプロイを行います。

## 📦 ワークフローファイル

### 1. 基本的なデプロイワークフロー

**ファイル**: [.github/workflows/deploy-ecs.yml](.github/workflows/deploy-ecs.yml)

**機能**:
- main/developブランチへのプッシュで自動実行
- OIDC認証によるAWSアクセス
- Dockerイメージのビルドとプッシュ
- ECSサービスの更新
- デプロイ安定性の確認

**トリガー**:
- `main` → prod環境
- `develop` → dev環境

### 2. 承認付きデプロイワークフロー

**ファイル**: [.github/workflows/deploy-with-approval.yml](.github/workflows/deploy-with-approval.yml)

**機能**:
- ビルドとテストの実行
- dev環境への自動デプロイ
- スモークテストの実行
- prod環境への承認付きデプロイ
- リリースタグの自動作成

**フロー**:
1. `build-and-test` ジョブ（テスト、Lint実行）
2. `deploy-dev` ジョブ（dev環境にデプロイ）
3. `deploy-prod` ジョブ（承認後にprod環境にデプロイ）
4. `notify` ジョブ（デプロイ結果の通知）

## 🔒 セキュリティ

### OIDC認証

AWS Access KeyやSecret Keyを使用せず、OIDCで一時的な認証情報を取得：

```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::${{ secrets.AWS_ACCOUNT_ID }}:role/github-actions-role-dev
    aws-region: ap-northeast-1
```

### ブランチ制限

CDK設定でデプロイ可能なブランチを制限：

```typescript
// cdk/lib/config/dev.ts
github: {
  owner: 'shinobu-takahata',
  repository: 'project-template',
  branches: ['main', 'develop']  // これらのブランチのみ許可
}
```

### IAM権限

最小権限の原則に基づき、必要な権限のみを付与：
- ECR: イメージのプッシュ/プル
- ECS: タスク定義の登録とサービスの更新
- IAM: PassRole（ECSタスクロール用）

## 🔧 カスタマイズ

### 環境変数の追加

タスク定義に環境変数を追加する場合：

```typescript
// cdk/lib/stacks/compute-stack.ts
environment: {
  ENV: config.envName,
  LOG_LEVEL: config.envName === 'prod' ? 'INFO' : 'DEBUG',
  CUSTOM_VAR: 'value'  // 追加
}
```

### デプロイタイムアウトの変更

```yaml
- name: Deploy Amazon ECS task definition
  uses: aws-actions/amazon-ecs-deploy-task-definition@v1
  with:
    wait-for-service-stability: true
    wait-for-minutes: 15  # デフォルト: 10分
```

### 通知の追加

Slackへの通知を追加：

```yaml
- name: Notify Slack
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

## 🐛 トラブルシューティング

### OIDC認証エラー

```
Error: Not authorized to perform sts:AssumeRoleWithWebIdentity
```

**解決方法**:
1. IAMロールの信頼関係を確認
2. ブランチ名が許可リストに含まれているか確認
3. CDKスタックを再デプロイ

### ECRプッシュエラー

```
denied: User is not authorized to perform: ecr:PutImage
```

**解決方法**:
1. IAMロールにECR権限があるか確認
2. ECRリポジトリが存在するか確認

### ECSデプロイ失敗

```
service was unable to place a task
```

**解決方法**:
1. CloudWatch Logsでエラーを確認
2. タスク定義のリソース制限を確認
3. セキュリティグループ設定を確認

詳細は [GitHub Actions デプロイメントガイド](./github-actions-deployment.md) を参照してください。

## 📊 モニタリング

### デプロイ状況の確認

```bash
# ECSサービスの状態確認
aws ecs describe-services \
  --cluster backend-cluster-dev \
  --services backend-service-dev \
  --region ap-northeast-1

# タスクの確認
aws ecs list-tasks \
  --cluster backend-cluster-dev \
  --service-name backend-service-dev \
  --region ap-northeast-1
```

### ログの確認

```bash
# CloudWatch Logsの確認
aws logs tail /ecs/backend-dev --follow
```

## 📚 関連ドキュメント

- [GitHub Actions デプロイメントガイド](./github-actions-deployment.md) - 詳細な設定手順
- [AWS CDK ドキュメント](../cdk/README_cdk.md) - インフラ構成
- [バックエンド README](../README/README_backend.md) - アプリケーション詳細

## 🎯 ベストプラクティス

1. **ブランチ戦略**
   - `develop`: 開発環境への自動デプロイ
   - `main`: 本番環境への承認付きデプロイ

2. **イメージタグ**
   - Git SHA をタグとして使用（トレーサビリティ）
   - `latest`タグは補助的に使用

3. **デプロイ検証**
   - ヘルスチェックの実装
   - スモークテストの実行
   - サービス安定性の確認

4. **ロールバック**
   - デプロイ失敗時の自動ロールバック有効化
   - 以前のタスク定義リビジョンへの手動ロールバック可能

## 🔄 手動ロールバック

デプロイに問題がある場合、以前のバージョンにロールバック：

```bash
# 以前のタスク定義リビジョンを確認
aws ecs list-task-definitions \
  --family-prefix backend-dev \
  --sort DESC

# 特定のリビジョンにロールバック
aws ecs update-service \
  --cluster backend-cluster-dev \
  --service backend-service-dev \
  --task-definition backend-dev:5  # リビジョン番号を指定
```

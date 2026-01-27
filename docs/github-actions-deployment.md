# GitHub Actions ECSデプロイ設定ガイド

このドキュメントでは、GitHub ActionsからOIDC認証を使用してAmazon ECSにデプロイする設定方法を説明します。

## 前提条件

1. CDKスタックがデプロイされていること（OIDC ProviderとIAMロールが作成済み）
2. GitHub リポジトリが `shinobu-takahata/project-template` であること
3. AWSアカウントIDが取得済みであること

## 1. GitHub Secretsの設定

GitHubリポジトリの Settings > Secrets and variables > Actions に以下のSecretを追加します：

### 必須のSecret

| Secret名 | 説明 | 例 |
|---------|------|-----|
| `AWS_ACCOUNT_ID` | AWSアカウントID | `123456789012` |

> **注意**: OIDC認証を使用するため、AWS Access KeyやSecret Keyは不要です。

## 2. CDKスタックの出力値を確認

デプロイ後、以下のCDK出力値を確認してください：

```bash
cd cdk
npx cdk deploy ComputeStack-dev --outputs-file outputs.json
```

確認すべき出力値：
- `GithubActionsRoleArn`: GitHub ActionsがAssumeするIAMロールのARN
- `EcrRepositoryUri`: ECRリポジトリのURI
- `EcsClusterName`: ECSクラスター名
- `EcsServiceName`: ECSサービス名

## 3. ワークフローの構成

### デプロイフロー

```
┌─────────────────┐
│  Push to Branch │
│  (main/develop) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Checkout Code   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Set Environment │
│ Variables       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Configure AWS   │
│ (OIDC Auth)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Login to ECR    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Build & Push    │
│ Docker Image    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Download Task   │
│ Definition      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Update Task Def │
│ (New Image)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Deploy to ECS   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Wait for        │
│ Stability       │
└─────────────────┘
```

### ブランチとデプロイ環境のマッピング

| ブランチ | デプロイ環境 | IAMロール |
|---------|------------|----------|
| `main` | `prod` | `github-actions-role-prod` |
| `develop` | `dev` | `github-actions-role-dev` |

## 4. IAMロールの権限

CDKで作成されるGitHub Actions用IAMロールには以下の権限が付与されています：

### ECR権限
- `ecr:GetAuthorizationToken` - ECRへの認証
- `ecr:BatchCheckLayerAvailability` - レイヤーの存在確認
- `ecr:GetDownloadUrlForLayer` - イメージのダウンロード
- `ecr:BatchGetImage` - イメージの取得
- `ecr:PutImage` - イメージのプッシュ
- `ecr:InitiateLayerUpload` - レイヤーアップロード開始
- `ecr:UploadLayerPart` - レイヤーアップロード
- `ecr:CompleteLayerUpload` - レイヤーアップロード完了

### ECS権限
- `ecs:RegisterTaskDefinition` - タスク定義の登録
- `ecs:DescribeTaskDefinition` - タスク定義の取得
- `ecs:DescribeServices` - サービス情報の取得
- `ecs:UpdateService` - サービスの更新

### IAM権限
- `iam:PassRole` - ECSタスク実行ロールの渡し

## 5. ワークフローのトリガー

### 自動デプロイ
以下のブランチにプッシュすると自動的にデプロイが実行されます：
- `main` → prod環境
- `develop` → dev環境

### 手動デプロイ
GitHub リポジトリの Actions タブから、`workflow_dispatch` イベントを使用して手動でワークフローを実行できます。

## 6. 初回デプロイの流れ

### 推奨フロー（確実で安全）

1. **GitHub Secretsを設定**
   ```bash
   gh secret set AWS_ACCOUNT_ID -b "YOUR_ACCOUNT_ID"
   ```

2. **初回イメージをECRにプッシュ**
   ```bash
   ./scripts/initial-push.sh
   ```
   環境を選択（dev/prod）すると、イメージをビルドしてECRにプッシュします。

3. **desiredCountを2に設定**
   ```typescript
   // cdk/lib/config/dev.ts
   ecs: {
     desiredCount: 2,  // 0 → 2に変更
     minCapacity: 2,   // 0 → 2に変更
   }
   ```

4. **CDKスタックをデプロイ**
   ```bash
   cd cdk
   npx cdk deploy --all
   ```
   イメージが既にECRにあるため、ECSタスクがすぐに起動します。✅

5. **以降は自動デプロイ**
   ```bash
   git add .
   git commit -m "feat: new feature"
   git push origin develop
   ```
   GitHub Actionsが自動的にデプロイを実行します。

### 代替フロー（GitHub Actionsのみ）

CDKを先にデプロイし、GitHub Actionsで初回イメージをプッシュする場合：

1. CDKデプロイ（desiredCount=0）
2. `git push`でGitHub Actions実行（イメージプッシュ）
3. desiredCount=2に変更してCDK再デプロイ

> **注意**: この方法では、一度タスク起動が失敗するため、推奨フローの方が確実です。

## 7. デプロイの確認

### デプロイ状況の確認方法

#### GitHub Actionsの画面で確認
1. GitHubリポジトリの `Actions` タブにアクセス
2. 最新のワークフロー実行を選択
3. 各ステップの実行結果を確認

#### AWSコンソールで確認
1. ECS コンソールにアクセス
2. クラスター → サービスを選択
3. デプロイメントタブでデプロイ状況を確認

#### CLIで確認
```bash
# サービスの状態確認
aws ecs describe-services \
  --cluster backend-cluster-dev \
  --services backend-service-dev \
  --region ap-northeast-1

# タスク一覧確認
aws ecs list-tasks \
  --cluster backend-cluster-dev \
  --service-name backend-service-dev \
  --region ap-northeast-1

# タスクの詳細確認
aws ecs describe-tasks \
  --cluster backend-cluster-dev \
  --tasks <task-arn> \
  --region ap-northeast-1
```

## 7. トラブルシューティング

### よくある問題と解決方法

#### 1. OIDC認証エラー
**エラー**: `Error: Not authorized to perform sts:AssumeRoleWithWebIdentity`

**原因**: 
- OIDCプロバイダーが正しく設定されていない
- IAMロールの信頼関係が正しくない
- ブランチ名が許可されていない

**解決方法**:
1. CDKスタックを再デプロイ
2. IAMロールの信頼関係を確認
3. `cdk/lib/config/dev.ts` のブランチ設定を確認

```typescript
github: {
  owner: 'shinobu-takahata',
  repository: 'project-template',
  branches: ['main', 'develop']  // デプロイを許可するブランチ
}
```

#### 2. ECRプッシュエラー
**エラー**: `denied: User: ... is not authorized to perform: ecr:PutImage`

**原因**: IAMロールにECR権限が不足

**解決方法**: CDKスタックを確認して再デプロイ

#### 3. ECSデプロイ失敗
**エラー**: `service backend-service-dev was unable to place a task`

**原因**: 
- タスク定義のリソース不足
- セキュリティグループの設定ミス
- サブネットの容量不足

**解決方法**:
1. CloudWatch Logsでエラーログを確認
2. ECSイベントタブでエラー詳細を確認
3. セキュリティグループのインバウンドルールを確認

#### 4. イメージが見つからない
**エラー**: `CannotPullContainerError: Error response from daemon`

**原因**: 
- ECRリポジトリにイメージが存在しない
- タスク実行ロールにECR権限がない

**解決方法**:
1. ECRリポジトリにイメージが存在するか確認
```bash
aws ecr describe-images \
  --repository-name backend-dev \
  --region ap-northeast-1
```
2. タスク実行ロールのポリシーを確認

## 8. セキュリティのベストプラクティス

### 1. OIDC認証の使用
- ❌ AWS Access KeyとSecret Keyを使用しない
- ✅ OIDC認証を使用して一時的な認証情報を取得

### 2. 最小権限の原則
- IAMロールには必要最小限の権限のみを付与
- リソースベースのポリシーを使用（可能な場合）

### 3. ブランチ制限
- デプロイを特定のブランチからのみ許可
- プルリクエストからのデプロイは禁止

### 4. タグ管理
- Git SHAをイメージタグとして使用
- `latest` タグは補助的に使用

## 9. 高度な設定

### カスタム通知の追加

Slackやメール通知を追加する場合：

```yaml
- name: Notify Slack
  if: always()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: 'Deployment to ${{ env.ENVIRONMENT }}: ${{ job.status }}'
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### ロールバック機能

デプロイ失敗時に自動ロールバック：

```yaml
- name: Rollback on failure
  if: failure()
  run: |
    aws ecs update-service \
      --cluster ${{ env.ECS_CLUSTER }} \
      --service ${{ env.ECS_SERVICE }} \
      --force-new-deployment \
      --region ${{ env.AWS_REGION }}
```

### 環境変数の動的設定

```yaml
- name: Set runtime environment variables
  run: |
    cat > .env << EOF
    ENVIRONMENT=${{ env.ENVIRONMENT }}
    GIT_SHA=${{ github.sha }}
    GIT_REF=${{ github.ref }}
    DEPLOYED_AT=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    EOF
```

## 10. 参考資料

- [GitHub Actions OIDC with AWS](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)
- [AWS ECS Deploy Task Definition Action](https://github.com/aws-actions/amazon-ecs-deploy-task-definition)
- [AWS CDK IAM Module](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_iam-readme.html)

# フェーズ7: CI/CD統合 - 要求内容

## 概要
GitHub ActionsからAWSリソース（ECR、ECS）へのデプロイを可能にするためのIAMロールを作成します。

## 背景
- フェーズ5でECRリポジトリとECSサービスが構築済み
- GitHub Actionsを使用したCI/CDパイプラインを構築するための認証基盤が必要
- OIDC（OpenID Connect）を使用してセキュアな認証を実現

## 機能要件

### 7.1 GitHub Actions用OIDC Providerの作成
- **URL**: `https://token.actions.githubusercontent.com`
- **Audience**: `sts.amazonaws.com`
- AWSアカウントに1つのみ作成（既存の場合は再利用）

### 7.2 GitHub Actions用IAMロールの作成
以下の権限を持つIAMロールを作成：

#### ECR関連権限
- `ecr:GetAuthorizationToken`
- `ecr:BatchCheckLayerAvailability`
- `ecr:GetDownloadUrlForLayer`
- `ecr:BatchGetImage`
- `ecr:PutImage`
- `ecr:InitiateLayerUpload`
- `ecr:UploadLayerPart`
- `ecr:CompleteLayerUpload`

#### ECS関連権限
- `ecs:RegisterTaskDefinition`
- `ecs:DescribeTaskDefinition`
- `ecs:DescribeServices`
- `ecs:UpdateService`
- `iam:PassRole`（タスクロール・タスク実行ロール用）

### 7.3 信頼ポリシーの設定
- GitHubリポジトリを制限
- 許可するブランチ: `main`、`develop`
- 形式: `repo:organization/repository:ref:refs/heads/branch`

## 非機能要件

### セキュリティ
- 最小権限の原則に従う
- 特定のリポジトリ・ブランチのみからのアクセスを許可
- IAMポリシーは必要なリソースのみに限定

### 運用性
- 環境（dev/prod）ごとに異なる信頼ポリシーを設定可能
- GitHubリポジトリ情報は環境設定で管理

## 受け入れ条件
1. OIDC Providerが正常に作成されること
2. IAMロールが適切な権限を持って作成されること
3. GitHub Actionsから`aws sts get-caller-identity`が成功すること
4. CDK synthが成功すること
5. CDK diffで変更内容が確認できること

## 制約事項
- OIDC Providerはアカウントに1つのみ（既存の場合は再利用またはインポート）
- GitHub Enterprise Serverは対象外（GitHub.com のみ）
- 本フェーズではGitHub Actionsワークフローファイルの作成は含まない（別タスク）

## 依存関係
- フェーズ5: ComputeStack（ECRリポジトリ、ECSサービス）が作成済みであること

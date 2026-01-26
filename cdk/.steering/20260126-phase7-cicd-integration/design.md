# フェーズ7: CI/CD統合 - 設計書

## 概要
GitHub ActionsからのECSデプロイを可能にするOIDC認証基盤を実装します。

## 実装アプローチ

### 方針
- ComputeStackに GitHub Actions用のOIDCプロバイダーとIAMロールを追加
- 環境設定（EnvConfig）にGitHubリポジトリ情報を追加
- 環境ごとに異なるブランチ制限を設定可能にする

## 変更対象ファイル

### 1. 環境設定の拡張
**ファイル**: `lib/config/env-config.ts`

```typescript
// 追加する型定義
export interface EnvConfig {
  // ... 既存の設定 ...

  // GitHub Actions CI/CD設定
  github?: {
    owner: string;           // GitHubオーナー（組織またはユーザー）
    repository: string;      // リポジトリ名
    branches: string[];      // 許可するブランチ（例: ['main', 'develop']）
  };
}
```

### 2. 開発環境設定
**ファイル**: `lib/config/dev.ts`

```typescript
github: {
  owner: 'your-organization',
  repository: 'your-repository',
  branches: ['main', 'develop']
}
```

### 3. 本番環境設定
**ファイル**: `lib/config/prod.ts`

```typescript
github: {
  owner: 'your-organization',
  repository: 'your-repository',
  branches: ['main']  // 本番は main のみ
}
```

### 4. ComputeStack への追加
**ファイル**: `lib/stacks/compute-stack.ts`

#### 4.1 OIDC Provider
```typescript
// GitHub Actions OIDC Provider
const githubProvider = new iam.OpenIdConnectProvider(this, 'GithubOidcProvider', {
  url: 'https://token.actions.githubusercontent.com',
  clientIds: ['sts.amazonaws.com'],
  thumbprints: ['ffffffffffffffffffffffffffffffffffffffff']  // GitHub用
});
```

**注意**: OIDC Providerはアカウントに1つのみ存在可能。既存の場合は `fromOpenIdConnectProviderArn` でインポート。

#### 4.2 IAM Role
```typescript
const githubActionsRole = new iam.Role(this, 'GithubActionsRole', {
  roleName: `github-actions-role-${config.envName}`,
  assumedBy: new iam.FederatedPrincipal(
    githubProvider.openIdConnectProviderArn,
    {
      StringEquals: {
        'token.actions.githubusercontent.com:aud': 'sts.amazonaws.com'
      },
      StringLike: {
        'token.actions.githubusercontent.com:sub': [
          `repo:${config.github.owner}/${config.github.repository}:ref:refs/heads/main`,
          `repo:${config.github.owner}/${config.github.repository}:ref:refs/heads/develop`
        ]
      }
    },
    'sts:AssumeRoleWithWebIdentity'
  )
});
```

#### 4.3 IAM Policy（ECR）
```typescript
githubActionsRole.addToPolicy(new iam.PolicyStatement({
  effect: iam.Effect.ALLOW,
  actions: [
    'ecr:GetAuthorizationToken'
  ],
  resources: ['*']
}));

githubActionsRole.addToPolicy(new iam.PolicyStatement({
  effect: iam.Effect.ALLOW,
  actions: [
    'ecr:BatchCheckLayerAvailability',
    'ecr:GetDownloadUrlForLayer',
    'ecr:BatchGetImage',
    'ecr:PutImage',
    'ecr:InitiateLayerUpload',
    'ecr:UploadLayerPart',
    'ecr:CompleteLayerUpload'
  ],
  resources: [this.ecrRepository.repositoryArn]
}));
```

#### 4.4 IAM Policy（ECS）
```typescript
githubActionsRole.addToPolicy(new iam.PolicyStatement({
  effect: iam.Effect.ALLOW,
  actions: [
    'ecs:RegisterTaskDefinition',
    'ecs:DescribeTaskDefinition',
    'ecs:DescribeServices',
    'ecs:UpdateService'
  ],
  resources: ['*']  // タスク定義は事前にARNが分からないため
}));

// PassRole（タスク実行ロール・タスクロール用）
githubActionsRole.addToPolicy(new iam.PolicyStatement({
  effect: iam.Effect.ALLOW,
  actions: ['iam:PassRole'],
  resources: [
    executionRole.roleArn,
    taskRole.roleArn
  ],
  conditions: {
    StringEquals: {
      'iam:PassedToService': 'ecs-tasks.amazonaws.com'
    }
  }
}));
```

#### 4.5 CfnOutput
```typescript
new CfnOutput(this, 'GithubActionsRoleArn', {
  value: githubActionsRole.roleArn,
  description: 'GitHub Actions IAM Role ARN',
  exportName: `${config.envName}-GithubActionsRoleArn`
});

new CfnOutput(this, 'GithubOidcProviderArn', {
  value: githubProvider.openIdConnectProviderArn,
  description: 'GitHub OIDC Provider ARN',
  exportName: `${config.envName}-GithubOidcProviderArn`
});
```

## アーキテクチャ図

```
GitHub Actions
     │
     │ OIDC Token
     ▼
┌─────────────────────────────────────────────┐
│  AWS STS                                    │
│  (AssumeRoleWithWebIdentity)                │
│                                             │
│  検証:                                      │
│  - OIDC Provider thumbprint                 │
│  - audience: sts.amazonaws.com              │
│  - subject: repo:org/repo:ref:refs/heads/*  │
└─────────────────────────────────────────────┘
     │
     │ Temporary Credentials
     ▼
┌─────────────────────────────────────────────┐
│  IAM Role: github-actions-role-{env}        │
│                                             │
│  Permissions:                               │
│  - ECR: Push/Pull images                    │
│  - ECS: Register task definition            │
│  - ECS: Update service                      │
│  - IAM: PassRole (task roles)               │
└─────────────────────────────────────────────┘
     │
     ├──────────────────┬──────────────────┐
     ▼                  ▼                  ▼
┌─────────┐      ┌──────────┐      ┌───────────┐
│   ECR   │      │   ECS    │      │    IAM    │
│ (Push)  │      │ (Deploy) │      │ (PassRole)│
└─────────┘      └──────────┘      └───────────┘
```

## セキュリティ考慮事項

### 1. 最小権限の原則
- ECR権限は特定リポジトリのみに限定
- ECSのUpdateServiceは特定クラスター・サービスに限定可能（必要に応じて）
- PassRoleは特定のロールのみに限定

### 2. ブランチ制限
- dev環境: `main`, `develop` ブランチからのデプロイを許可
- prod環境: `main` ブランチのみからのデプロイを許可

### 3. OIDC Provider
- GitHub.comの公式thumbprintを使用
- audienceは`sts.amazonaws.com`に固定

## 影響範囲

### 変更されるリソース
| リソース | 変更内容 |
|---------|---------|
| EnvConfig | github設定の追加 |
| ComputeStack | OIDC Provider、IAMロールの追加 |
| dev.ts | github設定の追加 |
| prod.ts | github設定の追加 |

### 依存関係
- ECRリポジトリ（既存）→ IAMポリシーで参照
- タスク実行ロール（既存）→ PassRoleで参照
- タスクロール（既存）→ PassRoleで参照

## テスト方法

### 1. CDK Synth
```bash
cd cdk && npx cdk synth --context env=dev
```

### 2. CDK Diff
```bash
cd cdk && npx cdk diff ComputeStack-dev --context env=dev
```

### 3. デプロイ後の検証
GitHub Actionsから以下を実行して認証が成功することを確認：
```yaml
- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::ACCOUNT_ID:role/github-actions-role-dev
    aws-region: ap-northeast-1

- run: aws sts get-caller-identity
```

## 注意事項

1. **OIDC Providerの重複**
   - 同一URLのOIDC Providerはアカウントに1つのみ
   - 複数環境（dev/prod）で共有、または最初の環境でのみ作成

2. **GitHub Enterprise Server**
   - 本設計はGitHub.com専用
   - GitHub Enterprise Serverの場合はURLが異なる

3. **Thumbprint**
   - GitHub Actions用のthumbprintは固定値を使用
   - CDK v2.160.0以降では自動計算もサポート

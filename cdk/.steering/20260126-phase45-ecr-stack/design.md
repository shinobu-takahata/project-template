# フェーズ4.5: ECRスタック - 設計書

## 概要
ECRリポジトリを管理する独立したスタック（EcrStack）を作成します。
このスタックは他のスタックに依存せず、最初にデプロイされます。

## アーキテクチャ

```
┌─────────────────────────────────────────┐
│  EcrStack                               │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  ECR Repository                   │ │
│  │  - backend-{env}                  │ │
│  │  - Image Scan: Enabled            │ │
│  │  - Lifecycle: Keep 10 images      │ │
│  │  - Encryption: AES256             │ │
│  │  - Removal Policy: RETAIN         │ │
│  └───────────────────────────────────┘ │
│                                         │
│  CfnOutput:                             │
│  - EcrRepositoryUri                     │
│  - EcrRepositoryArn                     │
│  - EcrRepositoryName                    │
└─────────────────────────────────────────┘
          │
          │ Fn.importValue
          ▼
┌─────────────────────────────────────────┐
│  ComputeStack                           │
│  - ECS Task Definition                  │
│    (uses ECR image)                     │
└─────────────────────────────────────────┘
```

## ファイル構成

### 新規作成ファイル
```
lib/
└── stacks/
    └── ecr-stack.ts          # EcrStack本体
```

### 変更ファイル
```
bin/
└── app.ts                    # EcrStackの追加
```

## 詳細設計

### 1. ecr-stack.ts

#### 1.1 インターフェース定義
```typescript
import * as cdk from 'aws-cdk-lib';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import { Construct } from 'constructs';
import { EnvConfig } from '../config/env-config';

export interface EcrStackProps extends cdk.StackProps {
  config: EnvConfig;
}

export class EcrStack extends cdk.Stack {
  public readonly repository: ecr.Repository;

  constructor(scope: Construct, id: string, props: EcrStackProps) {
    super(scope, id, props);
    // ...
  }
}
```

#### 1.2 ECRリポジトリの作成
```typescript
// Backend ECR Repository
this.repository = new ecr.Repository(this, 'BackendRepository', {
  repositoryName: `backend-${props.config.envName}`,

  // イメージスキャン設定
  imageScanOnPush: true,

  // タグの変更可否
  imageTagMutability: ecr.TagMutability.MUTABLE,

  // ライフサイクルポリシー（最新10イメージのみ保持）
  lifecycleRules: [
    {
      rulePriority: 1,
      description: 'Keep last 10 images',
      maxImageCount: 10
    }
  ],

  // 暗号化設定
  encryption: ecr.RepositoryEncryption.AES_256,

  // 削除ポリシー（誤削除防止）
  removalPolicy: cdk.RemovalPolicy.RETAIN,

  // 自動削除無効化（Retainと併用）
  autoDeleteImages: false
});
```

#### 1.3 CfnOutput（スタック間連携）
```typescript
// ECRリポジトリURI
new cdk.CfnOutput(this, 'EcrRepositoryUri', {
  value: this.repository.repositoryUri,
  description: 'ECR Repository URI',
  exportName: `${props.config.envName}-EcrRepositoryUri`
});

// ECRリポジトリARN
new cdk.CfnOutput(this, 'EcrRepositoryArn', {
  value: this.repository.repositoryArn,
  description: 'ECR Repository ARN',
  exportName: `${props.config.envName}-EcrRepositoryArn`
});

// ECRリポジトリ名
new cdk.CfnOutput(this, 'EcrRepositoryName', {
  value: this.repository.repositoryName,
  description: 'ECR Repository Name',
  exportName: `${props.config.envName}-EcrRepositoryName`
});
```

### 2. app.ts の変更

#### 2.1 EcrStackのインポート
```typescript
import { EcrStack } from '../lib/stacks/ecr-stack';
```

#### 2.2 EcrStackのインスタンス化
```typescript
// Phase 4.5: ECR Stack
const ecrStack = new EcrStack(app, `EcrStack-${envName}`, {
  env,
  config
});
```

#### 2.3 依存関係設定
```typescript
// ComputeStackがEcrStackに依存
computeStack.addDependency(ecrStack);
```

#### 2.4 全体のデプロイ順序
```typescript
// デプロイ順序:
// 1. NetworkStack (依存なし)
// 2. SecurityStack (依存なし)
// 3. DatabaseStack (NetworkStackに依存)
// 4. EcrStack (依存なし) ← 新規
// 5. ComputeStack (NetworkStack, SecurityStack, DatabaseStack, EcrStackに依存)
```

### 3. ComputeStackでのECR参照

#### 3.1 ECRリポジトリURIのインポート
```typescript
// ComputeStack内
const ecrRepositoryUri = cdk.Fn.importValue(`${config.envName}-EcrRepositoryUri`);
const ecrRepositoryArn = cdk.Fn.importValue(`${config.envName}-EcrRepositoryArn`);
```

#### 3.2 タスク定義でのイメージ指定
```typescript
// fromEcrRepositoryではなく、fromRegistryで指定
taskDefinition.addContainer('app', {
  image: ecs.ContainerImage.fromRegistry(ecrRepositoryUri),
  // ...
});
```

**注意**: `fromEcrRepository` はRepositoryオブジェクトが必要なため、クロススタック参照では使えません。
代わりに `fromRegistry` でURIを直接指定します。

### 4. GitHub ActionsからのECRアクセス（Phase 7で実装）

Phase 7のCI/CD統合では、以下のように参照します：

```typescript
// CI/CDスタック or ComputeStack内
const ecrRepositoryArn = cdk.Fn.importValue(`${config.envName}-EcrRepositoryArn`);

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
  resources: [ecrRepositoryArn]
}));
```

## ライフサイクルポリシー詳細

### 保持ルール
```typescript
lifecycleRules: [
  {
    rulePriority: 1,
    description: 'Keep last 10 images',
    maxImageCount: 10
  }
]
```

### 動作
- イメージが10個を超えると、古いイメージから自動削除
- タグ付きイメージも対象
- 削除前にイメージが使用中でないことを確認

### カスタマイズ例（必要に応じて）
```typescript
// 30日以上経過したuntaggedイメージを削除
{
  rulePriority: 2,
  description: 'Remove untagged images older than 30 days',
  tagStatus: ecr.TagStatus.UNTAGGED,
  maxImageAge: cdk.Duration.days(30)
}
```

## セキュリティ考慮事項

### 1. 暗号化
- AES256でイメージを暗号化
- KMS CMKも使用可能（コスト増）

### 2. イメージスキャン
- プッシュ時に自動スキャン
- 脆弱性検出時はECRコンソールで確認可能

### 3. アクセス制御
- IAMポリシーで厳密に制御
- リポジトリポリシーは不要（同一アカウント内）

### 4. 削除保護
- RemovalPolicy: RETAIN
- 誤ってスタック削除してもリポジトリは残る

## 初回デプロイフロー

### 1. EcrStackのデプロイ
```bash
cd cdk
npx cdk deploy EcrStack-dev --context env=dev
```

### 2. ダミーイメージのプッシュ（手動）
```bash
# ECR認証
aws ecr get-login-password --region ap-northeast-1 | \
  docker login --username AWS --password-stdin <account>.dkr.ecr.ap-northeast-1.amazonaws.com

# ダミーイメージのビルド
docker build -t backend-dev:latest .

# タグ付け
docker tag backend-dev:latest <account>.dkr.ecr.ap-northeast-1.amazonaws.com/backend-dev:latest

# プッシュ
docker push <account>.dkr.ecr.ap-northeast-1.amazonaws.com/backend-dev:latest
```

### 3. ComputeStackのデプロイ
```bash
npx cdk deploy ComputeStack-dev --context env=dev
```

## テスト方法

### 1. CDK Synth
```bash
cd cdk
npx cdk synth EcrStack-dev --context env=dev
```

### 2. CDK Diff（初回）
```bash
npx cdk diff EcrStack-dev --context env=dev
```

### 3. デプロイ後の検証
```bash
# ECRリポジトリの確認
aws ecr describe-repositories --repository-names backend-dev

# CloudFormationスタックの確認
aws cloudformation describe-stacks --stack-name EcrStack-dev

# Exportsの確認
aws cloudformation list-exports | grep -E 'dev-Ecr'
```

## 注意事項

### 1. スタック削除時の挙動
- RemovalPolicy: RETAINのため、スタック削除してもリポジトリは残る
- 完全削除する場合は、先にリポジトリを手動削除する必要がある

### 2. リポジトリ名の変更
- リポジトリ名を変更すると新しいリポジトリが作成される
- 古いリポジトリは自動削除されない（RemovalPolicy: RETAIN）

### 3. マルチリージョン対応
- ECRリポジトリはリージョン単位
- 複数リージョンで運用する場合は、各リージョンにEcrStackをデプロイ

### 4. イメージレプリケーション
- 必要に応じてECRレプリケーションを設定可能
- 本設計では未実装（将来対応）

## コスト試算（月額）

### ストレージコスト
- 0.10 USD/GB/月
- 例: 10イメージ × 500MB = 5GB → 0.50 USD/月

### データ転送コスト
- VPCエンドポイント経由: 無料
- インターネット経由のプル: 0.09 USD/GB

### 合計目安
- **約 0.50 USD/月** （イメージサイズによる）

## 今後の拡張

### 1. マルチアプリケーション対応
- frontend用のECRリポジトリ追加
- batch用のECRリポジトリ追加

### 2. クロスアカウント対応
- リポジトリポリシーで他アカウントからのアクセス許可

### 3. イメージレプリケーション
- DR対策としてのマルチリージョンレプリケーション

### 4. イメージ署名
- AWS Signerによるイメージ署名と検証

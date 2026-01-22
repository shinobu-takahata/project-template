# フェーズ1: CDK基盤セットアップ - 設計書

## 概要
本ドキュメントでは、AWS CDKプロジェクトの初期化と基本構造の実装設計について詳述します。

## アーキテクチャ設計

### ディレクトリ構造
```
cdk/
├── bin/
│   └── app.ts                          # CDKアプリケーションのエントリーポイント
├── lib/
│   ├── stacks/                         # CDKスタック定義（フェーズ2以降で実装）
│   │   ├── network-stack.ts
│   │   ├── security-stack.ts
│   │   ├── database-stack.ts
│   │   ├── compute-stack.ts
│   │   └── monitoring-stack.ts
│   ├── constructs/                     # 再利用可能なConstruct（フェーズ2以降で実装）
│   │   ├── multi-az-vpc.ts
│   │   ├── aurora-cluster.ts
│   │   ├── ecs-fargate-service.ts
│   │   └── alb-with-waf.ts
│   └── config/                         # 環境設定
│       ├── env-config.ts               # 環境設定の型定義とユーティリティ
│       ├── dev.ts                      # 開発環境設定
│       └── prod.ts                     # 本番環境設定
├── cdk.json                            # CDK設定
├── tsconfig.json                       # TypeScript設定
├── package.json                        # 依存関係
└── README.md                           # CDKプロジェクトのドキュメント（任意）
```

## コンポーネント設計

### 1. 環境設定（config/）

#### 1.1 env-config.ts - 型定義と共通関数
```typescript
// 環境設定の型定義
export interface EnvConfig {
  // 基本設定
  envName: 'dev' | 'prod';
  region: string;

  // VPC設定
  vpcCidr: string;
  availabilityZones: string[];
  publicSubnetCidrs: string[];
  privateSubnetCidrs: string[];
  useVpcEndpoints: boolean;  // NAT Gatewayの代わりにVPCエンドポイントを使用

  // ECS設定
  ecs: {
    cpu: number;
    memory: number;
    desiredCount: number;
    minCapacity: number;
    maxCapacity: number;
  };

  // Aurora設定
  aurora: {
    instanceClass: string;
    backupRetentionDays: number;
    deletionProtection: boolean;
  };

  // ログ設定
  logRetentionDays: number;

  // ドメイン設定
  domainName: string;
}

// 環境設定取得関数
export function getEnvConfig(envName: string): EnvConfig {
  switch (envName) {
    case 'dev':
      return devConfig;
    case 'prod':
      return prodConfig;
    default:
      throw new Error(`Unknown environment: ${envName}`);
  }
}
```

**設計の意図**:
- TypeScriptの型システムを活用し、設定の型安全性を確保
- 環境ごとの設定を一元管理
- 環境追加時の拡張性を考慮

#### 1.2 dev.ts - 開発環境設定
```typescript
import { EnvConfig } from './env-config';

export const devConfig: EnvConfig = {
  envName: 'dev',
  region: 'ap-northeast-1',

  // VPC設定
  vpcCidr: '10.0.0.0/16',
  availabilityZones: ['ap-northeast-1a', 'ap-northeast-1c'],
  publicSubnetCidrs: ['10.0.1.0/24', '10.0.2.0/24'],
  privateSubnetCidrs: ['10.0.11.0/24', '10.0.12.0/24'],
  useVpcEndpoints: true,  // コスト最適化: NAT Gatewayの代わりにVPCエンドポイント

  // ECS設定（開発環境は低スペック）
  ecs: {
    cpu: 512,           // 0.5 vCPU
    memory: 1024,       // 1 GB
    desiredCount: 2,    // マルチAZ構成
    minCapacity: 2,
    maxCapacity: 10
  },

  // Aurora設定（開発環境はt4g.medium）
  aurora: {
    instanceClass: 'db.t4g.medium',
    backupRetentionDays: 7,
    deletionProtection: false  // 開発環境は削除保護なし
  },

  // ログ設定（開発環境は短期保持）
  logRetentionDays: 7,

  // ドメイン設定
  domainName: 'dev-api.example.com'
};
```

**設計の意図**:
- 開発環境はコスト削減を優先
- マルチAZ構成を維持し、本番環境との構成差異を最小化
- 削除保護を無効化し、環境の作り直しを容易に

#### 1.3 prod.ts - 本番環境設定
```typescript
import { EnvConfig } from './env-config';

export const prodConfig: EnvConfig = {
  envName: 'prod',
  region: 'ap-northeast-1',

  // VPC設定（開発環境とCIDRを分離）
  vpcCidr: '10.1.0.0/16',
  availabilityZones: ['ap-northeast-1a', 'ap-northeast-1c'],
  publicSubnetCidrs: ['10.1.1.0/24', '10.1.2.0/24'],
  privateSubnetCidrs: ['10.1.11.0/24', '10.1.12.0/24'],
  useVpcEndpoints: true,  // コスト最適化: NAT Gatewayの代わりにVPCエンドポイント

  // ECS設定（本番環境は高スペック）
  ecs: {
    cpu: 1024,          // 1 vCPU
    memory: 2048,       // 2 GB
    desiredCount: 2,    // マルチAZ構成
    minCapacity: 2,
    maxCapacity: 20     // スケーリング上限を高く
  },

  // Aurora設定（本番環境はr6g.large）
  aurora: {
    instanceClass: 'db.r6g.large',
    backupRetentionDays: 30,
    deletionProtection: true  // 本番環境は削除保護有効
  },

  // ログ設定（本番環境は長期保持）
  logRetentionDays: 30,

  // ドメイン設定
  domainName: 'api.example.com'
};
```

**設計の意図**:
- 本番環境はパフォーマンスと可用性を優先
- 削除保護を有効化し、誤削除を防止
- ログ保持期間を長く設定し、監査要件に対応

### 2. エントリーポイント（bin/app.ts）

```typescript
#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { getEnvConfig } from '../lib/config/env-config';

const app = new cdk.App();

// Context値から環境名を取得（デフォルト: dev）
const envName = app.node.tryGetContext('env') || 'dev';
const config = getEnvConfig(envName);

// AWS環境設定
const env = {
  account: process.env.CDK_DEFAULT_ACCOUNT,
  region: config.region
};

// スタック作成の準備（フェーズ2以降で実装）
// 例:
// const networkStack = new NetworkStack(app, `NetworkStack-${envName}`, {
//   env,
//   config
// });

// CDKアプリケーションの合成
app.synth();
```

**設計の意図**:
- Context値で環境を切り替え可能（`--context env=dev`または`--context env=prod`）
- デフォルトは開発環境（dev）
- 環境ごとにスタック名を分離（`-${envName}`サフィックス）
- AWS環境設定は環境変数から取得（CDK_DEFAULT_ACCOUNT、CDK_DEFAULT_REGION）

**使用例**:
```bash
# 開発環境の合成
cdk synth --context env=dev

# 本番環境の合成
cdk synth --context env=prod

# デフォルト（dev）
cdk synth
```

### 3. CDK設定（cdk.json）

```json
{
  "app": "npx ts-node --prefer-ts-exts bin/app.ts",
  "watch": {
    "include": [
      "**"
    ],
    "exclude": [
      "README.md",
      "cdk*.json",
      "**/*.d.ts",
      "**/*.js",
      "tsconfig.json",
      "package*.json",
      "yarn.lock",
      "node_modules",
      "test"
    ]
  },
  "context": {
    "@aws-cdk/aws-lambda:recognizeLayerVersion": true,
    "@aws-cdk/core:checkSecretUsage": true,
    "@aws-cdk/core:target-partitions": [
      "aws",
      "aws-cn"
    ],
    "@aws-cdk-containers/ecs-service-extensions:enableDefaultLogDriver": true,
    "@aws-cdk/aws-ec2:uniqueImdsv2TemplateName": true,
    "@aws-cdk/aws-ecs:arnFormatIncludesClusterName": true,
    "@aws-cdk/aws-iam:minimizePolicies": true,
    "@aws-cdk/core:validateSnapshotRemovalPolicy": true,
    "@aws-cdk/aws-codepipeline:crossAccountKeyAliasStackSafeResourceName": true,
    "@aws-cdk/aws-s3:createDefaultLoggingPolicy": true,
    "@aws-cdk/aws-sns-subscriptions:restrictSqsDescryption": true,
    "@aws-cdk/aws-apigateway:disableCloudWatchRole": true,
    "@aws-cdk/core:enablePartitionLiterals": true,
    "@aws-cdk/aws-events:eventsTargetQueueSameAccount": true,
    "@aws-cdk/aws-iam:standardizedServicePrincipals": true,
    "@aws-cdk/aws-ecs:disableExplicitDeploymentControllerForCircuitBreaker": true,
    "@aws-cdk/aws-iam:importedRoleStackSafeDefaultPolicyName": true,
    "@aws-cdk/aws-s3:serverAccessLogsUseBucketPolicy": true,
    "@aws-cdk/aws-route53-patters:useCertificate": true,
    "@aws-cdk/customresources:installLatestAwsSdkDefault": false,
    "@aws-cdk/aws-rds:databaseProxyUniqueResourceName": true,
    "@aws-cdk/aws-codedeploy:removeAlarmsFromDeploymentGroup": true,
    "@aws-cdk/aws-apigateway:authorizerChangeDeploymentLogicalId": true,
    "@aws-cdk/aws-ec2:launchTemplateDefaultUserData": true,
    "@aws-cdk/aws-secretsmanager:useAttachedSecretResourcePolicyForSecretTargetAttachments": true,
    "@aws-cdk/aws-redshift:columnId": true,
    "@aws-cdk/aws-stepfunctions-tasks:enableEmrServicePolicyV2": true,
    "@aws-cdk/aws-ec2:restrictDefaultSecurityGroup": true,
    "@aws-cdk/aws-apigateway:requestValidatorUniqueId": true,
    "@aws-cdk/aws-kms:aliasNameRef": true,
    "@aws-cdk/aws-autoscaling:generateLaunchTemplateInsteadOfLaunchConfig": true,
    "@aws-cdk/core:includePrefixInUniqueNameGeneration": true,
    "@aws-cdk/aws-efs:denyAnonymousAccess": true,
    "@aws-cdk/aws-opensearchservice:enableOpensearchMultiAzWithStandby": true,
    "@aws-cdk/aws-lambda-nodejs:useLatestRuntimeVersion": true,
    "@aws-cdk/aws-efs:mountTargetOrderInsensitiveLogicalId": true,
    "@aws-cdk/aws-rds:auroraClusterChangeScopeOfInstanceParameterGroupWithEachParameters": true,
    "@aws-cdk/aws-appsync:useArnForSourceApiAssociationIdentifier": true,
    "@aws-cdk/aws-rds:preventRenderingDeprecatedCredentials": true,
    "@aws-cdk/aws-codepipeline-actions:useNewDefaultBranchForCodeCommitSource": true,
    "@aws-cdk/aws-cloudwatch-actions:changeLambdaPermissionLogicalIdForLambdaAction": true,
    "@aws-cdk/aws-codepipeline:crossAccountKeysDefaultValueToFalse": true,
    "@aws-cdk/aws-codepipeline:defaultPipelineTypeToV2": true,
    "@aws-cdk/aws-kms:reduceCrossAccountRegionPolicyScope": true,
    "@aws-cdk/aws-eks:nodegroupNameAttribute": true,
    "@aws-cdk/aws-ec2:ebsDefaultGp3Volume": true,
    "@aws-cdk/aws-ecs:removeDefaultDeploymentAlarm": true,
    "@aws-cdk/custom-resources:logApiResponseDataPropertyTrueDefault": false,
    "@aws-cdk/aws-s3:keepNotificationInImportedBucket": false
  }
}
```

**設計の意図**:
- CDK v2の最新feature flagsを有効化
- セキュリティベストプラクティスを適用（IMDSv2、IAMポリシーの最小化など）
- ウォッチモードでの自動再ビルドをサポート

### 4. TypeScript設定（tsconfig.json）

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": [
      "es2020"
    ],
    "declaration": true,
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "noImplicitThis": true,
    "alwaysStrict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": false,
    "inlineSourceMap": true,
    "inlineSources": true,
    "experimentalDecorators": true,
    "strictPropertyInitialization": false,
    "typeRoots": [
      "./node_modules/@types"
    ],
    "esModuleInterop": true,
    "skipLibCheck": true,
    "resolveJsonModule": true
  },
  "exclude": [
    "node_modules",
    "cdk.out"
  ]
}
```

**設計の意図**:
- 厳格な型チェックを有効化（`strict: true`）
- ES2020をターゲットとし、最新のJavaScript機能をサポート
- ソースマップを含めることでデバッグを容易に

### 5. 依存関係（package.json）

```json
{
  "name": "cdk",
  "version": "0.1.0",
  "bin": {
    "cdk": "bin/app.js"
  },
  "scripts": {
    "build": "tsc",
    "watch": "tsc -w",
    "test": "jest",
    "cdk": "cdk"
  },
  "devDependencies": {
    "@types/jest": "^29.5.0",
    "@types/node": "^20.0.0",
    "jest": "^29.5.0",
    "ts-jest": "^29.1.0",
    "aws-cdk": "^2.120.0",
    "ts-node": "^10.9.1",
    "typescript": "~5.3.0"
  },
  "dependencies": {
    "aws-cdk-lib": "^2.120.0",
    "constructs": "^10.0.0",
    "source-map-support": "^0.5.21"
  }
}
```

**設計の意図**:
- CDK v2の最新安定版を使用（2.120.0以上）
- TypeScript 5.3系を使用（最新の型機能をサポート）
- テストフレームワーク（Jest）を含める（フェーズ後半で使用）

## データフロー

### 環境設定の読み込みフロー
```
1. cdk コマンド実行（例: cdk synth --context env=prod）
   ↓
2. bin/app.ts が実行される
   ↓
3. app.node.tryGetContext('env') でContext値から環境名を取得
   ↓
4. getEnvConfig(envName) で環境設定を読み込み
   ↓
5. config/prod.ts から prodConfig を返す
   ↓
6. スタック作成時に config を渡す
   ↓
7. 各スタック内で config のパラメータを参照
```

## セキュリティ設計

### S-1: シークレット管理
- データベース認証情報などのシークレットは設定ファイルに含めない
- Secrets Managerで管理（フェーズ4以降で実装）

### S-2: IAM権限
- CDKデプロイに必要な最小限の権限を定義
- 本番環境はMFA必須（AWSアカウントレベルで設定）

### S-3: タグ戦略
- すべてのリソースに環境タグを付与（Environment: dev/prod）
- プロジェクト識別タグ（Project: project-template）
- コスト配分タグ（CostCenter）

## パフォーマンス設計

### P-1: 合成時間
- スタック数を適切に分割し、合成時間を最小化
- 依存関係を明確にし、並列デプロイを可能に

### P-2: デプロイ時間
- スタック間の依存関係を最小化
- 不要なリソース更新を避ける

## テスト戦略

### T-1: 型チェック
- TypeScriptコンパイラによる静的型チェック（`npm run build`）

### T-2: 合成テスト
- CDK合成が正常に完了することを確認（`cdk synth`）

### T-3: ユニットテスト（後続フェーズで実装）
- Jestを使用したスタック・Constructのユニットテスト

## 運用設計

### O-1: デプロイ手順
```bash
# 開発環境
cd cdk
npm install
npm run build
cdk synth --context env=dev
cdk deploy --all --context env=dev

# 本番環境
cdk synth --context env=prod
cdk deploy --all --context env=prod --require-approval broadening
```

### O-2: 環境変数管理
- AWS認証情報: AWS_PROFILE、AWS_REGION
- デプロイ対象環境: --context env=<環境名>

### O-3: ロールバック
- CloudFormationスタックのロールバック機能を活用
- 必要に応じて前のバージョンのCDKコードから再デプロイ

## コスト最適化設計

### C-1: VPCエンドポイント戦略
- NAT Gatewayの代わりにVPCエンドポイントを使用
- 年間約$420のコスト削減

### C-2: 環境別リソース設定
- 開発環境は低スペック（t4g系）
- 本番環境は高スペック（r6g系）

## 変更管理

### 設定変更時の手順
1. 該当する設定ファイル（dev.ts または prod.ts）を編集
2. `npm run build`でTypeScriptをコンパイル
3. `cdk diff --context env=<環境名>`で差分を確認
4. `cdk deploy --context env=<環境名>`でデプロイ

### 環境追加時の手順
1. `lib/config/`に新しい環境設定ファイルを作成（例: staging.ts）
2. `env-config.ts`の`getEnvConfig`関数に分岐を追加
3. `EnvConfig`型の`envName`に新しい環境を追加

## 制約事項

### 既知の制約
- Context値は文字列のみサポート（複雑なオブジェクトは不可）
- 環境ごとに完全に独立したリソースを作成（共有リソースなし）

## 次のステップ

本フェーズ完了後、以下のフェーズに進みます：
1. **フェーズ2**: ネットワーク基盤（VPC、Route53、VPCエンドポイント）
2. **フェーズ3**: セキュリティ基盤（GuardDuty、Config、WAF）
3. **フェーズ4**: データベース基盤（Aurora PostgreSQL）
4. **フェーズ5**: コンピューティング基盤（ECR、ALB、ECS + Fluent Bit）
5. **フェーズ6**: 監視・ロギング基盤（CloudWatch、SNS、S3）
6. **フェーズ7**: CI/CD統合（GitHub Actions）

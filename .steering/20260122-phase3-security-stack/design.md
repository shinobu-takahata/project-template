# フェーズ3: セキュリティ基盤 - 設計

## 概要
SecurityStackを実装し、GuardDuty、AWS Config、WAFの3つのセキュリティサービスを統合します。

## アーキテクチャ

### コンポーネント構成

```
SecurityStack-{envName}
├── GuardDuty Detector
│   └── データソース設定（VPC Flow Logs, DNS, CloudTrail, S3）
│
├── AWS Config
│   ├── Config Recorder
│   ├── Delivery Channel
│   ├── S3 Bucket（記録用）
│   └── IAM Role
│
└── WAF Web ACL
    ├── AWSManagedRulesCommonRuleSet
    ├── AWSManagedRulesKnownBadInputsRuleSet
    └── AWSManagedRulesSQLiRuleSet
```

## 実装アプローチ

### 1. SecurityStackの作成

**ファイル**: `lib/stacks/security-stack.ts`

**責務**:
- GuardDuty Detectorの作成
- AWS Configの設定（Recorder、Delivery Channel、S3バケット、IAMロール）
- WAF Web ACLの作成

**エクスポート**:
- `webAclArn`: WAF Web ACLのARN（フェーズ5で使用）

### 2. GuardDuty Detector

**実装方法**:
```typescript
import * as guardduty from 'aws-cdk-lib/aws-guardduty';

const detector = new guardduty.CfnDetector(this, 'GuardDutyDetector', {
  enable: true,
  dataSources: {
    s3Logs: { enable: true },
    kubernetes: { auditLogs: { enable: false } },
    malwareProtection: { scanEc2InstanceWithFindings: { ebsVolumes: { enable: false } } }
  }
});
```

**特徴**:
- VPCフローログ、DNS、CloudTrailは自動的に有効
- S3ログ保護を明示的に有効化
- Kubernetes監査ログは無効（EKS未使用）
- マルウェア保護は無効（コスト最適化）

### 3. AWS Config

#### 3.1 S3バケット（Config記録用）

**実装方法**:
```typescript
import * as s3 from 'aws-cdk-lib/aws-s3';

const configBucket = new s3.Bucket(this, 'ConfigBucket', {
  bucketName: `config-${config.envName}-${this.account}`,
  encryption: s3.BucketEncryption.S3_MANAGED,
  versioned: true,
  blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
  removalPolicy: config.removalPolicy.s3Buckets === 'DESTROY'
    ? RemovalPolicy.DESTROY
    : RemovalPolicy.RETAIN,
  autoDeleteObjects: config.removalPolicy.s3Buckets === 'DESTROY',
});
```

**バケットポリシー**:
- AWS Configサービスからの書き込みを許可
- バケットACL取得を許可

#### 3.2 IAM Role（Config Recorder用）

**実装方法**:
```typescript
import * as iam from 'aws-cdk-lib/aws-iam';

const configRole = new iam.Role(this, 'ConfigRole', {
  assumedBy: new iam.ServicePrincipal('config.amazonaws.com'),
  managedPolicies: [
    iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/ConfigRole')
  ]
});

configBucket.grantWrite(configRole);
```

**権限**:
- AWSマネージドポリシー: `AWS_ConfigRole`
- S3バケットへの書き込み権限

#### 3.3 Config Recorder

**実装方法**:
```typescript
import * as config from 'aws-cdk-lib/aws-config';

const recorder = new config.CfnConfigurationRecorder(this, 'ConfigRecorder', {
  name: `config-recorder-${config.envName}`,
  roleArn: configRole.roleArn,
  recordingGroup: {
    allSupported: true,
    includeGlobalResourceTypes: true
  }
});
```

**記録対象**:
- すべてのサポートされているリソースタイプ
- IAM、CloudFrontなどグローバルリソースを含む

#### 3.4 Delivery Channel

**実装方法**:
```typescript
const deliveryChannel = new config.CfnDeliveryChannel(this, 'DeliveryChannel', {
  name: `config-delivery-${config.envName}`,
  s3BucketName: configBucket.bucketName,
  configSnapshotDeliveryProperties: {
    deliveryFrequency: 'TwentyFour_Hours'
  }
});

deliveryChannel.addDependency(recorder);
```

**配信設定**:
- 配信先: Config S3バケット
- スナップショット頻度: 24時間ごと

### 4. WAF Web ACL

**実装方法**:
```typescript
import * as wafv2 from 'aws-cdk-lib/aws-wafv2';

const webAcl = new wafv2.CfnWebACL(this, 'WebACL', {
  scope: 'REGIONAL',
  defaultAction: { allow: {} },
  visibilityConfig: {
    sampledRequestsEnabled: true,
    cloudWatchMetricsEnabled: true,
    metricName: `WebACL-${config.envName}`
  },
  rules: [
    // ルール1: Common Rule Set
    {
      name: 'AWSManagedRulesCommonRuleSet',
      priority: 1,
      statement: {
        managedRuleGroupStatement: {
          vendorName: 'AWS',
          name: 'AWSManagedRulesCommonRuleSet'
        }
      },
      overrideAction: { none: {} },
      visibilityConfig: {
        sampledRequestsEnabled: true,
        cloudWatchMetricsEnabled: true,
        metricName: 'AWSManagedRulesCommonRuleSetMetric'
      }
    },
    // ルール2: Known Bad Inputs
    {
      name: 'AWSManagedRulesKnownBadInputsRuleSet',
      priority: 2,
      statement: {
        managedRuleGroupStatement: {
          vendorName: 'AWS',
          name: 'AWSManagedRulesKnownBadInputsRuleSet'
        }
      },
      overrideAction: { none: {} },
      visibilityConfig: {
        sampledRequestsEnabled: true,
        cloudWatchMetricsEnabled: true,
        metricName: 'AWSManagedRulesKnownBadInputsRuleSetMetric'
      }
    },
    // ルール3: SQL Injection
    {
      name: 'AWSManagedRulesSQLiRuleSet',
      priority: 3,
      statement: {
        managedRuleGroupStatement: {
          vendorName: 'AWS',
          name: 'AWSManagedRulesSQLiRuleSet'
        }
      },
      overrideAction: { none: {} },
      visibilityConfig: {
        sampledRequestsEnabled: true,
        cloudWatchMetricsEnabled: true,
        metricName: 'AWSManagedRulesSQLiRuleSetMetric'
      }
    }
  ]
});
```

**ルール説明**:
- **Common Rule Set**: 一般的な脅威をブロック（OWASP Top 10など）
- **Known Bad Inputs**: 既知の悪意のある入力パターンをブロック
- **SQLi Rule Set**: SQLインジェクション攻撃をブロック

**エクスポート**:
```typescript
new CfnOutput(this, 'WebAclArn', {
  value: webAcl.attrArn,
  description: 'WAF Web ACL ARN',
  exportName: `${config.envName}-WebAclArn`
});
```

## エントリーポイント（bin/app.ts）の更新

SecurityStackをアプリケーションに追加:

```typescript
import { SecurityStack } from '../lib/stacks/security-stack';

// SecurityStackの作成
const securityStack = new SecurityStack(app, `SecurityStack-${envName}`, {
  env,
  config
});
```

## データフロー

### AWS Config
```
AWSリソース変更
  ↓
Config Recorder（検出）
  ↓
Delivery Channel
  ↓
S3 Bucket（config-{envName}-{accountId}）
```

### GuardDuty
```
VPCフローログ/DNS/CloudTrail/S3ログ
  ↓
GuardDuty Detector（分析）
  ↓
脅威検出結果
  ↓
（フェーズ6でSNS通知を追加）
```

### WAF
```
HTTPリクエスト（ALB経由 - フェーズ5で関連付け）
  ↓
WAF Web ACL（ルール評価）
  ↓
Allow/Block判定
  ↓
CloudWatch Metrics
```

## 影響範囲

### 新規ファイル
- `lib/stacks/security-stack.ts`

### 更新ファイル
- `bin/app.ts`（SecurityStackのインポートと作成）

### 依存関係
- Phase 1: 環境設定（env-config.ts）
- Phase 2: VPC（GuardDutyがVPCフローログを利用）

## セキュリティ考慮事項

### GuardDuty
- デフォルトでVPCフローログ、DNS、CloudTrailを監視
- S3ログ保護を有効化
- 検出結果は後のフェーズでSNS通知

### AWS Config
- S3バケットは暗号化・バージョニング有効
- パブリックアクセスブロック
- IAMロールは最小権限

### WAF
- デフォルトアクション: Allow（正常なトラフィックを許可）
- マネージドルールセットで既知の脅威をブロック
- CloudWatch Metricsで監視可能

## コスト見積もり

### GuardDuty
- VPCフローログ分析: 約$1.00/GB
- CloudTrailイベント分析: 約$4.16/100万イベント
- S3ログ分析: 約$0.80/GB
- **月額概算**: $10-30（トラフィック量による）

### AWS Config
- 記録項目: 約$0.003/項目/月
- 100リソースの場合: 約$0.30/月
- S3ストレージ: 使用量による
- **月額概算**: $10-20

### WAF
- Web ACL: $5.00/月
- ルール: $1.00/ルール/月 × 3 = $3.00/月
- リクエスト: $0.60/100万リクエスト
- **月額概算**: $5-10（リクエスト量による）

**合計概算**: $25-60/月

## トラブルシューティング

### Config Recorderが起動しない
- IAMロールの権限を確認
- S3バケットポリシーを確認
- Delivery Channelの依存関係を確認

### WAFルールが厳しすぎる
- CloudWatch Metricsでブロック数を確認
- サンプリングされたリクエストを確認
- ルールの優先度を調整またはルールを無効化

### GuardDutyの検出結果が多すぎる
- 検出結果を確認し、誤検知を特定
- 信頼するIPアドレスを除外リストに追加
- 不要なデータソースを無効化

## 次のステップ

SecurityStack実装後:
1. ビルド・デプロイテスト
2. GuardDutyの検出結果を確認
3. AWS Configの記録を確認
4. WAF Web ACLの動作確認
5. フェーズ4（DatabaseStack）に進む

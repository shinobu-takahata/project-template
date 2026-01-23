# フェーズ4: データベース基盤 - 設計

## 概要
DatabaseStackを実装し、Aurora PostgreSQL Clusterとその関連リソースを構築します。
プライマリ・レプリカのマルチAZ構成により、高可用性と読み取りスケーラビリティを実現します。

## アーキテクチャ

### コンポーネント構成

```
DatabaseStack-{envName}
├── Secrets Manager
│   └── データベース認証情報（dbadmin + 自動生成パスワード）
│
├── DBサブネットグループ
│   ├── プライベートサブネット（AZ-1）
│   └── プライベートサブネット（AZ-2）
│
├── DBセキュリティグループ
│   └── PostgreSQLポート（5432）のインバウンドルール
│
└── Aurora PostgreSQL Cluster
    ├── Primary Instance（AZ-1）
    ├── Replica Instance（AZ-2）
    ├── KMS暗号化
    ├── 自動バックアップ
    ├── CloudWatch Logs統合
    └── Performance Insights（本番環境のみ）
```

### ネットワーク配置

```
VPC (10.0.0.0/16 or 10.1.0.0/16)
│
├── AZ-1 (ap-northeast-1a)
│   └── プライベートサブネット (10.x.11.0/24)
│       └── Aurora Primary Instance
│
└── AZ-2 (ap-northeast-1c)
    └── プライベートサブネット (10.x.12.0/24)
        └── Aurora Replica Instance
```

## 実装アプローチ

### 1. DatabaseStackの作成

**ファイル**: `lib/stacks/database-stack.ts`

**責務**:
- Aurora PostgreSQL Clusterの作成（プライマリ + レプリカ）
- DBサブネットグループの作成
- DBセキュリティグループの作成
- Secrets Managerによる認証情報管理
- Performance Insightsの設定（本番環境のみ）
- CloudWatch Logsエクスポート

**Props インターフェース**:
```typescript
export interface DatabaseStackProps extends StackProps {
  config: EnvConfig;
  vpcId: string;           // NetworkStackからインポート
  privateSubnetIds: string[];  // NetworkStackからインポート
}
```

**エクスポート**:
- `dbClusterArn`: Auroraクラスタ ARN
- `dbClusterEndpoint`: 書き込みエンドポイント
- `dbClusterReadEndpoint`: 読み取りエンドポイント
- `dbSecretArn`: Secrets Manager ARN
- `dbSecurityGroupId`: DBセキュリティグループ ID

### 2. Secrets Manager（認証情報管理）

**実装方法**:
```typescript
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';

// データベース認証情報を自動生成
const dbSecret = new secretsmanager.Secret(this, 'DBSecret', {
  secretName: `${config.envName}/aurora/credentials`,
  description: `Aurora database credentials for ${config.envName}`,
  generateSecretString: {
    secretStringTemplate: JSON.stringify({ username: 'dbadmin' }),
    generateStringKey: 'password',
    excludeCharacters: '"@/\\',  // 特殊文字を制限
    passwordLength: 32,
    excludePunctuation: false
  },
  removalPolicy: config.removalPolicy.database === 'DESTROY'
    ? RemovalPolicy.DESTROY
    : RemovalPolicy.RETAIN
});
```

**シークレット構造**:
```json
{
  "username": "dbadmin",
  "password": "自動生成された32文字のパスワード"
}
```

**削除ポリシー**:
- 開発環境: `DESTROY`（即座に削除）
- 本番環境: `RETAIN`（削除保護）

### 3. DBサブネットグループ

**実装方法**:
```typescript
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { Fn } from 'aws-cdk-lib';

// NetworkStackからVPCをインポート
const vpc = ec2.Vpc.fromVpcAttributes(this, 'VPC', {
  vpcId: Fn.importValue(`${config.envName}-VpcId`),
  availabilityZones: config.availabilityZones,
  privateSubnetIds: [
    Fn.importValue(`${config.envName}-PrivateSubnetId1`),
    Fn.importValue(`${config.envName}-PrivateSubnetId2`)
  ]
});

// サブネットグループ（L1 Constructで作成）
const dbSubnetGroup = new rds.CfnDBSubnetGroup(this, 'DBSubnetGroup', {
  dbSubnetGroupName: `db-subnet-group-${config.envName}`,
  dbSubnetGroupDescription: `DB subnet group for ${config.envName}`,
  subnetIds: [
    Fn.importValue(`${config.envName}-PrivateSubnetId1`),
    Fn.importValue(`${config.envName}-PrivateSubnetId2`)
  ],
  tags: [
    { key: 'Environment', value: config.envName },
    { key: 'Project', value: 'project-template' },
    { key: 'ManagedBy', value: 'CDK' }
  ]
});
```

**特徴**:
- プライベートサブネットのみ使用
- マルチAZ構成（2つのAZ）
- NetworkStackからサブネットIDをインポート

### 4. DBセキュリティグループ

**実装方法**:
```typescript
// DBセキュリティグループ
const dbSecurityGroup = new ec2.SecurityGroup(this, 'DBSecurityGroup', {
  vpc,
  securityGroupName: `db-sg-${config.envName}`,
  description: 'Security group for Aurora database',
  allowAllOutbound: true
});

// PostgreSQLポート（5432）へのインバウンドルール
// 注意: ECSセキュリティグループはフェーズ5で作成されるため、
// ここでは送信元をVPC CIDR全体として設定
dbSecurityGroup.addIngressRule(
  ec2.Peer.ipv4(config.vpcCidr),
  ec2.Port.tcp(5432),
  'Allow PostgreSQL access from VPC'
);

Tags.of(dbSecurityGroup).add('Environment', config.envName);
Tags.of(dbSecurityGroup).add('Project', 'project-template');
Tags.of(dbSecurityGroup).add('ManagedBy', 'CDK');
```

**インバウンドルール**:
- ポート: 5432（PostgreSQL）
- 送信元: VPC CIDR全体（フェーズ5でECSセキュリティグループに変更予定）

**アウトバウンドルール**:
- すべて許可

**将来の改善**（フェーズ5で実装）:
```typescript
// フェーズ5で、ECSセキュリティグループからのアクセスのみに制限
dbSecurityGroup.addIngressRule(
  ecsSecurityGroup,
  ec2.Port.tcp(5432),
  'Allow PostgreSQL access from ECS tasks'
);
```

### 5. Aurora PostgreSQL Cluster

**実装方法**:
```typescript
import * as rds from 'aws-cdk-lib/aws-rds';

// Aurora Clusterの作成
const dbCluster = new rds.DatabaseCluster(this, 'AuroraCluster', {
  engine: rds.DatabaseClusterEngine.auroraPostgres({
    version: rds.AuroraPostgresEngineVersion.VER_15_4  // PostgreSQL 15互換
  }),
  credentials: rds.Credentials.fromSecret(dbSecret),
  writer: rds.ClusterInstance.provisioned('WriterInstance', {
    instanceType: ec2.InstanceType.of(
      ec2.InstanceClass.fromString(config.aurora.instanceClass.split('.')[1]),
      ec2.InstanceSize.fromString(config.aurora.instanceClass.split('.')[2])
    ),
    availabilityZone: config.availabilityZones[0],  // AZ-1
    enablePerformanceInsights: config.envName === 'prod',
    performanceInsightRetention: config.envName === 'prod'
      ? rds.PerformanceInsightRetention.DEFAULT  // 7日間（無料）
      : undefined
  }),
  readers: [
    rds.ClusterInstance.provisioned('ReaderInstance', {
      instanceType: ec2.InstanceType.of(
        ec2.InstanceClass.fromString(config.aurora.instanceClass.split('.')[1]),
        ec2.InstanceSize.fromString(config.aurora.instanceClass.split('.')[2])
      ),
      availabilityZone: config.availabilityZones[1],  // AZ-2
      enablePerformanceInsights: config.envName === 'prod',
      performanceInsightRetention: config.envName === 'prod'
        ? rds.PerformanceInsightRetention.DEFAULT
        : undefined
    })
  ],
  vpc,
  vpcSubnets: {
    subnets: vpc.privateSubnets
  },
  securityGroups: [dbSecurityGroup],
  backup: {
    retention: Duration.days(config.aurora.backupRetentionDays),
    preferredWindow: '03:00-04:00'  // JST 12:00-13:00（深夜）
  },
  preferredMaintenanceWindow: 'sun:19:00-sun:20:00',  // JST 月曜 04:00-05:00
  storageEncrypted: true,
  deletionProtection: config.aurora.deletionProtection,
  removalPolicy: config.removalPolicy.database === 'DESTROY'
    ? RemovalPolicy.DESTROY
    : config.removalPolicy.database === 'SNAPSHOT'
    ? RemovalPolicy.SNAPSHOT
    : RemovalPolicy.RETAIN,
  cloudwatchLogsExports: ['postgresql'],  // PostgreSQLログをCloudWatchに出力
  cloudwatchLogsRetention: logs.RetentionDays.fromString(
    `${config.logRetentionDays}_DAYS`
  )
});

Tags.of(dbCluster).add('Environment', config.envName);
Tags.of(dbCluster).add('Project', 'project-template');
Tags.of(dbCluster).add('ManagedBy', 'CDK');
```

**主要設定**:

| 設定項目 | 開発環境 | 本番環境 |
|---------|---------|---------|
| インスタンスクラス | db.t4g.small | db.r6g.large |
| バックアップ保持 | 7日間 | 30日間 |
| 削除保護 | 無効 | 有効 |
| Performance Insights | 無効 | 有効（7日間） |
| 削除ポリシー | DESTROY | SNAPSHOT |

**エンジンバージョン**:
- PostgreSQL 15互換（Aurora PostgreSQL 15.4）

**暗号化**:
- KMSによる保存時暗号化（storageEncrypted: true）
- デフォルトKMSキー使用

**バックアップ**:
- 自動バックアップウィンドウ: 03:00-04:00 UTC（JST 12:00-13:00）
- メンテナンスウィンドウ: 日曜 19:00-20:00 UTC（月曜 04:00-05:00 JST）

**ログ**:
- PostgreSQLログをCloudWatch Logsにエクスポート
- 保持期間: 環境設定に従う（dev: 7日、prod: 30日）

### 6. エクスポート

**実装方法**:
```typescript
import { CfnOutput } from 'aws-cdk-lib';

// DBクラスタARN
new CfnOutput(this, 'DbClusterArn', {
  value: dbCluster.clusterArn,
  description: 'Aurora cluster ARN',
  exportName: `${config.envName}-DbClusterArn`
});

// DBクラスタエンドポイント（書き込み用）
new CfnOutput(this, 'DbClusterEndpoint', {
  value: dbCluster.clusterEndpoint.hostname,
  description: 'Aurora cluster writer endpoint',
  exportName: `${config.envName}-DbClusterEndpoint`
});

// DBクラスタ読み取りエンドポイント
new CfnOutput(this, 'DbClusterReadEndpoint', {
  value: dbCluster.clusterReadEndpoint.hostname,
  description: 'Aurora cluster reader endpoint',
  exportName: `${config.envName}-DbClusterReadEndpoint`
});

// DBシークレットARN
new CfnOutput(this, 'DbSecretArn', {
  value: dbSecret.secretArn,
  description: 'Database credentials secret ARN',
  exportName: `${config.envName}-DbSecretArn`
});

// DBセキュリティグループID
new CfnOutput(this, 'DbSecurityGroupId', {
  value: dbSecurityGroup.securityGroupId,
  description: 'Database security group ID',
  exportName: `${config.envName}-DbSecurityGroupId`
});
```

## エントリーポイント（bin/app.ts）の更新

DatabaseStackをアプリケーションに追加:

```typescript
import { DatabaseStack } from '../lib/stacks/database-stack';

// DatabaseStackの作成（NetworkStackの後）
const databaseStack = new DatabaseStack(app, `DatabaseStack-${envName}`, {
  env,
  config
});
```

**依存関係**:
- NetworkStackから VPC ID とプライベートサブネット ID をインポート

## データフロー

### データベース接続フロー（将来実装）
```
ECS Task（フェーズ5で実装）
  ↓
Secrets Managerから認証情報取得
  ↓
DBセキュリティグループ（5432ポート）
  ↓
Aurora Primary（書き込み）
  ↓
Aurora Replica（読み取り）
```

### バックアップフロー
```
Aurora Cluster
  ↓
自動バックアップ（毎日 03:00-04:00 UTC）
  ↓
Auroraバックアップストレージ（保持期間: dev=7日、prod=30日）
  ↓
削除時（本番のみ）
  ↓
最終スナップショット作成
```

### ログフロー
```
Aurora PostgreSQL
  ↓
CloudWatch Logs
  ↓
ログ保持（dev: 7日、prod: 30日）
```

### Performance Insights（本番のみ）
```
Aurora Cluster
  ↓
パフォーマンスデータ収集
  ↓
Performance Insights
  ↓
データ保持（7日間、無料）
```

## 影響範囲

### 新規ファイル
- `lib/stacks/database-stack.ts`

### 更新ファイル
- `bin/app.ts`（DatabaseStackのインポートと作成）

### 依存関係

**インポート**:
- Phase 1: 環境設定（env-config.ts）
- Phase 2: NetworkStack（VPC、プライベートサブネット）

**エクスポート**（フェーズ5で使用）:
- DBクラスタエンドポイント → ECSタスク環境変数
- DBシークレットARN → ECSタスクロールの権限
- DBセキュリティグループID → インバウンドルール更新

## セキュリティ考慮事項

### 認証情報管理
- Secrets Managerで認証情報を自動生成
- パスワード: 32文字、記号を含む
- 特殊文字を制限（`"@/\`を除外）してエスケープ問題を回避
- 本番環境ではシークレットを削除保護

### ネットワークセキュリティ
- プライベートサブネットにのみ配置
- インターネットから直接アクセス不可
- VPC内からのアクセスのみ許可（現時点ではVPC CIDR全体）
- フェーズ5でECSセキュリティグループからのみアクセス可能に制限

### 暗号化
- **保存時暗号化**: KMS（デフォルトキー）
- **転送時暗号化**: SSL/TLS接続を推奨（アプリケーション側で設定）

### バックアップ
- 自動バックアップ有効化
- 削除保護（本番環境のみ）
- スナップショット作成（本番環境の削除時）

### 監査
- CloudWatch Logsへのログエクスポート
- Performance Insights（本番環境のみ）でパフォーマンス監視

## コスト見積もり

### 開発環境（dev）
- **Aurora インスタンス（db.t4g.small）**: 約$30/月 × 2インスタンス = $60/月
- **ストレージ**: 約$0.10/GB/月（100GBで約$10/月）
- **バックアップストレージ**: 無料（データベースサイズまで）
- **Secrets Manager**: $0.40/シークレット/月
- **CloudWatch Logs**: 使用量による（約$5/月）
- **月額概算**: $75-90

### 本番環境（prod）
- **Aurora インスタンス（db.r6g.large）**: 約$150/月 × 2インスタンス = $300/月
- **ストレージ**: 約$0.10/GB/月（500GBで約$50/月）
- **バックアップストレージ**: 約$0.021/GB/月（30日保持で約$10/月）
- **Performance Insights**: 無料（7日間保持）
- **Secrets Manager**: $0.40/シークレット/月
- **CloudWatch Logs**: 使用量による（約$10/月）
- **月額概算**: $370-400

**コスト最適化のポイント**:
- 開発環境はt4gインスタンスを使用（Graviton2、低コスト）
- Performance Insightsは本番のみ有効化
- バックアップ保持期間を環境別に設定
- 不要な開発環境は削除可能（DESTROY設定）

## トラブルシューティング

### Aurora Clusterが起動しない
- DBサブネットグループの設定を確認
- プライベートサブネットが2つのAZに配置されているか確認
- セキュリティグループの設定を確認
- KMS暗号化キーの権限を確認

### Secrets Managerからパスワード取得に失敗
- シークレット名が正しいか確認（`${envName}/aurora/credentials`）
- IAMロールにSecrets Manager読み取り権限があるか確認（フェーズ5で設定）
- シークレットのJSON構造を確認

### データベース接続エラー
- セキュリティグループのインバウンドルールを確認
- VPC内からアクセスしているか確認
- エンドポイントが正しいか確認（書き込み/読み取り）
- 認証情報が正しいか確認

### Performance Insightsが表示されない（本番環境）
- 本番環境でデプロイされているか確認
- Performance Insightsが有効化されているか確認
- データ収集に時間がかかる場合がある（数分待つ）

### バックアップが作成されない
- バックアップ保持期間が0より大きいか確認
- バックアップウィンドウが設定されているか確認
- CloudFormation Stackのイベントログを確認

## 次のステップ

DatabaseStack実装後:
1. ビルド・デプロイテスト
2. Aurora Clusterの起動確認
3. Secrets Managerのシークレット確認
4. CloudWatch Logsのログ確認
5. Performance Insights確認（本番環境）
6. フェーズ5（ECSStack）に進む

フェーズ5では以下を実装します：
- ECS Cluster
- ECS Task Definition（データベース接続設定を含む）
- ECS Service
- Application Load Balancer
- ECSセキュリティグループ
- **DBセキュリティグループのインバウンドルール更新**（ECSセキュリティグループからのみアクセス許可）

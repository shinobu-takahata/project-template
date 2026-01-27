# フェーズ5: コンピューティング基盤 - 設計書

## 概要
ComputeStackを作成し、ALB、ECSクラスター、ECS Fargateサービスを構築する。
ECRリポジトリは別スタック（EcrStack）で管理され、本スタックから参照します。

## ファイル構成

### 新規作成ファイル
```
lib/
├── stacks/
│   └── compute-stack.ts          # メインのComputeStack
├── constructs/
│   ├── ecs-fargate-service.ts    # ECS Fargate Service Construct (オプション)
│   └── alb-with-waf.ts           # ALB + WAF Construct (オプション)
```

### 変更ファイル
```
bin/
└── app.ts                         # ComputeStackの追加
lib/
└── config/
    └── env-config.ts              # ALBログバケット設定の追加（必要に応じて）
```

## 詳細設計

### 1. compute-stack.ts

#### インポート・依存関係
- NetworkStackからVPC情報をFn.importValueで取得
- SecurityStackからWebAcl ARNをFn.importValueで取得
- DatabaseStackからSecrets Manager ARNをFn.importValueで取得
- EcrStackからECRリポジトリURIをFn.importValueで取得

#### 主要コンポーネント

##### 1.1 ECRリポジトリURIのインポート
```typescript
// EcrStackからECRリポジトリURIをインポート
const ecrRepositoryUri = cdk.Fn.importValue(`${config.envName}-EcrRepositoryUri`);
```

**注意**: ECRリポジトリ自体はEcrStack（Phase 4.5）で管理されます。

##### 1.2 ALBアクセスログ用S3バケット
```typescript
new s3.Bucket(this, 'AlbLogBucket', {
  bucketName: `alb-logs-${config.envName}-${account}`,
  encryption: s3.BucketEncryption.S3_MANAGED,
  blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
  lifecycleRules: [...]
});
```

##### 1.3 ALBセキュリティグループ
```typescript
new ec2.SecurityGroup(this, 'AlbSecurityGroup', {
  vpc,
  description: 'Security group for ALB',
  allowAllOutbound: true
});
// インバウンド: HTTP(80), HTTPS(443) from 0.0.0.0/0
```

##### 1.4 ECSセキュリティグループ
```typescript
new ec2.SecurityGroup(this, 'EcsSecurityGroup', {
  vpc,
  description: 'Security group for ECS tasks',
  allowAllOutbound: true
});
// インバウンド: 8000 from ALB SG
// アウトバウンド: 5432 to Aurora, 443 to HTTPS
```

##### 1.5 Application Load Balancer
```typescript
new elbv2.ApplicationLoadBalancer(this, 'ALB', {
  vpc,
  internetFacing: true,
  vpcSubnets: { subnetType: ec2.SubnetType.PUBLIC },
  securityGroup: albSecurityGroup
});
```

##### 1.6 ターゲットグループ
```typescript
new elbv2.ApplicationTargetGroup(this, 'TargetGroup', {
  vpc,
  port: 8000,
  protocol: elbv2.ApplicationProtocol.HTTP,
  targetType: elbv2.TargetType.IP,
  healthCheck: {
    path: '/health',
    interval: Duration.seconds(30),
    timeout: Duration.seconds(5),
    healthyThresholdCount: 2,
    unhealthyThresholdCount: 3
  }
});
```

##### 1.7 HTTPリスナー
```typescript
alb.addListener('HttpListener', {
  port: 80,
  protocol: elbv2.ApplicationProtocol.HTTP,
  defaultTargetGroups: [targetGroup]
});
```

##### 1.8 WAF関連付け
```typescript
new wafv2.CfnWebACLAssociation(this, 'WebACLAssociation', {
  resourceArn: alb.loadBalancerArn,
  webAclArn: webAclArn
});
```

##### 1.9 ECS Cluster
```typescript
new ecs.Cluster(this, 'EcsCluster', {
  vpc,
  clusterName: `cluster-${config.envName}`,
  containerInsights: true
});
```

##### 1.10 ECS Task Definition
```typescript
new ecs.FargateTaskDefinition(this, 'TaskDef', {
  cpu: config.ecs.cpu,
  memoryLimitMiB: config.ecs.memory,
  executionRole: executionRole,
  taskRole: taskRole
});
```

##### 1.11 メインコンテナ（FastAPI）
```typescript
taskDefinition.addContainer('app', {
  // ECRリポジトリURIを使用（クロススタック参照のためfromRegistryを使用）
  image: ecs.ContainerImage.fromRegistry(ecrRepositoryUri),
  portMappings: [{ containerPort: 8000 }],
  logging: ecs.LogDrivers.firelens({...}),
  secrets: {
    DATABASE_URL: ecs.Secret.fromSecretsManager(dbSecret)
  },
  environment: {
    ENV: config.envName
  }
});
```

**注意**: クロススタック参照のため、`fromEcrRepository`ではなく`fromRegistry`でURIを直接指定します。

##### 1.12 Fluent Bitサイドカー
```typescript
taskDefinition.addFirelensLogRouter('log-router', {
  image: ecs.ContainerImage.fromRegistry('amazon/aws-for-fluent-bit:stable'),
  firelensConfig: {
    type: ecs.FirelensLogRouterType.FLUENTBIT,
    options: {
      enableECSLogMetadata: true
    }
  }
});
```

##### 1.13 ECS Service
```typescript
new ecs.FargateService(this, 'Service', {
  cluster,
  taskDefinition,
  desiredCount: config.ecs.desiredCount,
  vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
  securityGroups: [ecsSecurityGroup],
  assignPublicIp: false
});
```

##### 1.14 Auto Scaling
```typescript
const scalableTarget = service.autoScaleTaskCount({
  minCapacity: config.ecs.minCapacity,
  maxCapacity: config.ecs.maxCapacity
});

scalableTarget.scaleOnCpuUtilization('CpuScaling', {
  targetUtilizationPercent: 70,
  scaleInCooldown: Duration.seconds(60),
  scaleOutCooldown: Duration.seconds(60)
});
```

### 2. IAMロール設計

#### タスク実行ロール (executionRole)
- `AmazonECSTaskExecutionRolePolicy` マネージドポリシー
- ECRからのイメージプル権限
- Secrets Manager読み取り権限
- CloudWatch Logs書き込み権限

#### タスクロール (taskRole)
- S3ログバケットへの書き込み権限
- CloudWatch Logs書き込み権限（Fluent Bit用）

### 3. スタック出力 (CfnOutput)
- ALB DNS名: `${config.envName}-AlbDnsName`
- ALB ARN: `${config.envName}-AlbArn`
- ECSクラスター名: `${config.envName}-EcsClusterName`
- ECSサービス名: `${config.envName}-EcsServiceName`
- ECSセキュリティグループID: `${config.envName}-EcsSecurityGroupId`

**注意**: ECRリポジトリURIはEcrStackから出力されます。

### 4. app.ts の変更
```typescript
import { ComputeStack } from '../lib/stacks/compute-stack';

// ComputeStackの作成
const computeStack = new ComputeStack(app, `ComputeStack-${envName}`, {
  env,
  config
});

// 依存関係を設定
computeStack.addDependency(networkStack);
computeStack.addDependency(securityStack);
computeStack.addDependency(databaseStack);
computeStack.addDependency(ecrStack);  // EcrStackへの依存を追加
```

**デプロイ順序**:
1. NetworkStack（依存なし）
2. SecurityStack（依存なし）
3. DatabaseStack（NetworkStackに依存）
4. EcrStack（依存なし）
5. ComputeStack（すべてのスタックに依存）

## セキュリティ考慮事項
1. ECSタスクはプライベートサブネットに配置（インターネット直接アクセス不可）
2. ALBのみがパブリックサブネットに配置
3. データベース接続情報はSecrets Managerで管理
4. WAFによるWeb攻撃対策
5. ECRイメージスキャンによる脆弱性検出
6. 最小権限の原則に基づくIAMロール設計

## 注意事項
- **ECRリポジトリはEcrStack（Phase 4.5）で管理**: ComputeStackデプロイ前にEcrStackのデプロイとイメージプッシュが必要
- EcrStackデプロイ後、ダミーイメージをECRにプッシュしてからComputeStackをデプロイする
- VPCエンドポイント経由でECR、Secrets Manager、CloudWatch Logsにアクセス
- HTTPS対応は証明書準備後に別途追加

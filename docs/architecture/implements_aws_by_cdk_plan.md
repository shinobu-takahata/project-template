# AWS CDK 実装計画書

## 概要
本ドキュメントは、[aws_infra.md](aws_infra.md)で定義されたAWSインフラストラクチャをAWS CDKで実装する際の計画を定義します。

## 実装方針

### 環境構成
- **開発環境（dev）と本番環境（prod）の2環境構成**
- 各環境は独立したVPCとリソースを持つ
- 環境固有のパラメータは設定ファイルまたはContext値で管理

### 実装の優先順位
1. **最優先**: Webアプリケーション基盤（VPC、ECS、Aurora、ALB）
2. **高優先度**: セキュリティ基盤（GuardDuty、Config、WAF）、監視（CloudWatch、SNS）
3. **中優先度**: ログ最適化（Fluent Bit、S3ログ保存）
4. **低優先度（後回し）**: Step Functions、EventBridge、Amplify

### セキュリティ
GuardDuty、AWS Config、WAFを初期実装に含めます。

### ログ戦略（コスト最適化）
- ERRORレベル以上 → CloudWatch Logs（即座の分析・アラート用）
- 全ログ → S3バケット（長期保存・監査用）
- Fluent Bitでログを振り分け

## CDKプロジェクト構造

```
cdk/
├── bin/
│   └── app.ts                          # CDKアプリケーションのエントリーポイント
├── lib/
│   ├── stacks/
│   │   ├── network-stack.ts            # VPC、サブネット、VPCエンドポイント、Route53
│   │   ├── security-stack.ts           # GuardDuty、Config、WAF
│   │   ├── database-stack.ts           # Aurora PostgreSQL
│   │   ├── compute-stack.ts            # ECS、Fargate、ALB、ECR、Fluent Bit
│   │   └── monitoring-stack.ts         # CloudWatch、SNS、S3（ログ保存）
│   ├── constructs/
│   │   ├── multi-az-vpc.ts             # マルチAZ VPC Construct
│   │   ├── aurora-cluster.ts           # Aurora Cluster Construct
│   │   ├── ecs-fargate-service.ts      # ECS Fargate Service + Fluent Bit Construct
│   │   └── alb-with-waf.ts             # ALB + WAF Construct
│   └── config/
│       ├── env-config.ts               # 環境設定の型定義
│       ├── dev.ts                      # 開発環境設定
│       └── prod.ts                     # 本番環境設定
├── cdk.json                            # CDK設定
├── tsconfig.json                       # TypeScript設定
└── package.json                        # 依存関係
```

## 実装順序

### フェーズ1: 基盤セットアップ（優先度：最高）

#### 1.1 CDKプロジェクト初期化
**目的**: CDKプロジェクトの基本構造を作成

**実装内容**:
- `cdk init app --language typescript`の実行（既存の場合はスキップ）
- 必要なディレクトリ構造の作成
  - `lib/stacks/`
  - `lib/constructs/`
  - `lib/config/`
- package.jsonへの依存関係追加
  ```json
  {
    "dependencies": {
      "aws-cdk-lib": "^2.120.0",
      "constructs": "^10.0.0"
    },
    "devDependencies": {
      "@types/node": "^20.0.0",
      "typescript": "^5.0.0",
      "aws-cdk": "^2.120.0"
    }
  }
  ```
- tsconfig.jsonの設定
- cdk.jsonの環境別設定

**成果物**:
- `cdk/bin/app.ts`
- `cdk/cdk.json`
- `cdk/tsconfig.json`
- `cdk/package.json`

**依存関係**: なし

---

#### 1.2 環境設定ファイル作成
**目的**: dev/prod環境の設定を定義

**実装内容**:
- 環境別パラメータの定義
  - VPC CIDR、サブネットCIDR
  - リージョン（ap-northeast-1）、AZ
  - ECSタスクリソース（CPU、メモリ）
  - Auroraインスタンスクラス
  - ログ保持期間
  - ドメイン名
- リソース命名規則の定義
- タグ戦略の定義

**成果物**:
- `cdk/lib/config/env-config.ts`（型定義）
- `cdk/lib/config/dev.ts`
- `cdk/lib/config/prod.ts`

**依存関係**: 1.1

---

### フェーズ2: ネットワーク基盤（優先度：最高）

#### 2.1 VPC Constructの実装
**目的**: マルチAZ構成のVPCを構築

**実装内容**:
- VPCの作成（ap-northeast-1、CIDR: 環境設定から取得）
- 2つのAvailability Zoneの選択
- パブリックサブネット × 2（各AZに1つ）
- プライベートサブネット × 2（各AZに1つ）- **インターネット接続なし**（Isolated Subnet）
- インターネットゲートウェイ（パブリックサブネット用）
- ルートテーブルの設定
- VPCフローログ（CloudWatch Logsへ）

**重要**: NAT Gatewayは作成しません。代わりにVPCエンドポイントを使用します（次セクション2.1.1）。

**成果物**:
- `cdk/lib/constructs/multi-az-vpc.ts`
- `cdk/lib/stacks/network-stack.ts`

**依存関係**: 1.2

**参考CDKリソース**:
```typescript
import * as ec2 from 'aws-cdk-lib/aws-ec2';

const vpc = new ec2.Vpc(this, 'VPC', {
  maxAzs: 2,
  natGateways: 0, // NAT Gatewayは使用しない（コスト最適化）
  subnetConfiguration: [
    {
      name: 'Public',
      subnetType: ec2.SubnetType.PUBLIC,
      cidrMask: 24
    },
    {
      name: 'Private',
      subnetType: ec2.SubnetType.PRIVATE_ISOLATED, // インターネット接続なし
      cidrMask: 24
    }
  ],
  flowLogs: {
    cloudwatch: {
      destination: ec2.FlowLogDestination.toCloudWatchLogs()
    }
  }
});
```

---

#### 2.1.1 VPCエンドポイントの作成（コスト最適化）
**目的**: NAT Gatewayの代わりにVPCエンドポイントを使用してAWSサービスにアクセス

**実装内容**:
- **Gateway型エンドポイント**（無料）:
  - **S3**: ログ保存、静的ファイルアクセス用
  - プライベートサブネットのルートテーブルに自動追加
- **Interface型エンドポイント**（有料: 約$7.2/月/個）:
  - **ECR API** (`com.amazonaws.ap-northeast-1.ecr.api`): ECRリポジトリAPI用
  - **ECR DKR** (`com.amazonaws.ap-northeast-1.ecr.dkr`): Dockerイメージプル用
  - **Secrets Manager** (`com.amazonaws.ap-northeast-1.secretsmanager`): DB認証情報取得用
  - **CloudWatch Logs** (`com.amazonaws.ap-northeast-1.logs`): ログ出力用
  - プライベートサブネットに配置（マルチAZ）
  - セキュリティグループ: ECSタスクからのHTTPS (443) アクセスを許可
  - プライベートDNSの有効化

**コスト比較**:
- NAT Gateway方式: 約$64/月（2個 × $32） + データ転送料
- VPCエンドポイント方式: 約$28.8/月（Interface型 × 4個） + $0（Gateway型）
- **削減額**: 約$35/月（年間約$420）

**成果物**:
- `cdk/lib/stacks/network-stack.ts`（追加）

**依存関係**: 2.1（VPC）

**参考CDKリソース**:
```typescript
import * as ec2 from 'aws-cdk-lib/aws-ec2';

// Gateway型エンドポイント（無料）
vpc.addGatewayEndpoint('S3Endpoint', {
  service: ec2.GatewayVpcEndpointAwsService.S3,
  subnets: [{ subnetType: ec2.SubnetType.PRIVATE_ISOLATED }]
});

// Interface型エンドポイント用セキュリティグループ
const vpcEndpointSg = new ec2.SecurityGroup(this, 'VpcEndpointSg', {
  vpc,
  description: 'Security group for VPC endpoints',
  allowAllOutbound: false
});

// ECSタスクからのHTTPSアクセスを許可（後でECSセキュリティグループから追加）
vpcEndpointSg.addIngressRule(
  ec2.Peer.ipv4(vpc.vpcCidrBlock),
  ec2.Port.tcp(443),
  'Allow HTTPS from VPC'
);

// ECR API エンドポイント
vpc.addInterfaceEndpoint('EcrApiEndpoint', {
  service: ec2.InterfaceVpcEndpointAwsService.ECR,
  subnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
  securityGroups: [vpcEndpointSg],
  privateDnsEnabled: true
});

// ECR DKR エンドポイント
vpc.addInterfaceEndpoint('EcrDkrEndpoint', {
  service: ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER,
  subnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
  securityGroups: [vpcEndpointSg],
  privateDnsEnabled: true
});

// Secrets Manager エンドポイント
vpc.addInterfaceEndpoint('SecretsManagerEndpoint', {
  service: ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
  subnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
  securityGroups: [vpcEndpointSg],
  privateDnsEnabled: true
});

// CloudWatch Logs エンドポイント
vpc.addInterfaceEndpoint('CloudWatchLogsEndpoint', {
  service: ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS,
  subnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
  securityGroups: [vpcEndpointSg],
  privateDnsEnabled: true
});
```

---

#### 2.2 Route 53 Hosted Zoneの設定
**目的**: カスタムドメインの管理

**実装内容**:
- Hosted Zoneの作成またはインポート（既存の場合）
- ACM証明書のDNS検証用レコード作成（手動または自動）
- ALB用Aレコード作成は後のフェーズで実施

**成果物**:
- `cdk/lib/stacks/network-stack.ts`（一部追加）

**依存関係**: 1.2

**注意**: ドメインは事前に取得済みであること

**参考CDKリソース**:
```typescript
import * as route53 from 'aws-cdk-lib/aws-route53';

const hostedZone = route53.HostedZone.fromLookup(this, 'HostedZone', {
  domainName: 'example.com'
});
```

---

### フェーズ3: セキュリティ基盤（優先度：高）

#### 3.1 GuardDutyの有効化
**目的**: 脅威検出サービスの有効化

**実装内容**:
- GuardDuty Detectorの有効化
- データソースの設定（VPCフローログ、DNS、CloudTrail）

**成果物**:
- `cdk/lib/stacks/security-stack.ts`

**依存関係**: 1.2

**参考CDKリソース**:
```typescript
import * as guardduty from 'aws-cdk-lib/aws-guardduty';

new guardduty.CfnDetector(this, 'GuardDutyDetector', {
  enable: true,
  dataSources: {
    s3Logs: { enable: true }
  }
});
```

---

#### 3.2 AWS Configの設定
**目的**: リソース構成の記録と監査

**実装内容**:
- Config Recorderの作成
- 記録対象リソースの設定（全リソース）
- S3バケット（Config記録用）の作成
- Delivery Channelの設定
- IAMロールの作成

**成果物**:
- `cdk/lib/stacks/security-stack.ts`（追加）

**依存関係**: 1.2

**参考CDKリソース**:
```typescript
import * as config from 'aws-cdk-lib/aws-config';

new config.CfnConfigurationRecorder(this, 'ConfigRecorder', {
  roleArn: role.roleArn,
  recordingGroup: {
    allSupported: true,
    includeGlobalResources: true
  }
});
```

---

#### 3.3 WAF Web ACLの作成（ALB用）
**目的**: Webアプリケーションファイアウォールの設定

**実装内容**:
- WAF Web ACLの作成（ALB用、リージョナル）
- 基本的なマネージドルールセットの追加
  - AWSManagedRulesCommonRuleSet
  - AWSManagedRulesKnownBadInputsRuleSet
  - AWSManagedRulesSQLiRuleSet（SQL injection対策）
- デフォルトアクション: Allow
- CloudWatch Metricsの有効化

**成果物**:
- `cdk/lib/stacks/security-stack.ts`（追加）

**依存関係**: 1.2

**注意**: ALBへの関連付けはフェーズ5.2で実施

**参考CDKリソース**:
```typescript
import * as wafv2 from 'aws-cdk-lib/aws-wafv2';

new wafv2.CfnWebACL(this, 'WebACL', {
  scope: 'REGIONAL',
  defaultAction: { allow: {} },
  rules: [
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
    }
  ]
});
```

---

### フェーズ4: データベース基盤（優先度：高）

#### 4.1 Aurora PostgreSQL Clusterの実装
**目的**: マルチAZ構成のAuroraデータベースを構築

**実装内容**:
- Aurora PostgreSQL クラスターの作成（プロビジョニング型）
  - エンジン: PostgreSQL 15互換
  - インスタンスクラス:
    - 開発環境: db.t4g.medium
    - 本番環境: db.r6g.large
  - プライマリインスタンス: AZ-1のプライベートサブネット
  - レプリカインスタンス: AZ-2のプライベートサブネット
- DBサブネットグループの作成
- セキュリティグループの作成（ECSからのアクセスのみ許可 - ポート5432）
- KMSキーによる暗号化
- 自動バックアップの設定
  - バックアップ保持期間: 7日（開発）、30日（本番）
  - バックアップウィンドウ: 深夜時間帯
- 削除保護の有効化（本番環境のみ）
- Secrets Managerでの認証情報管理
- Performance Insightsの有効化（本番環境）

**成果物**:
- `cdk/lib/constructs/aurora-cluster.ts`
- `cdk/lib/stacks/database-stack.ts`

**依存関係**: 2.1（VPC）

**参考CDKリソース**:
```typescript
import * as rds from 'aws-cdk-lib/aws-rds';
import * as ec2 from 'aws-cdk-lib/aws-ec2';

const cluster = new rds.DatabaseCluster(this, 'AuroraCluster', {
  engine: rds.DatabaseClusterEngine.auroraPostgres({
    version: rds.AuroraPostgresEngineVersion.VER_15_3
  }),
  writer: rds.ClusterInstance.provisioned('writer', {
    instanceType: ec2.InstanceType.of(
      ec2.InstanceClass.T4G,
      ec2.InstanceSize.MEDIUM
    )
  }),
  readers: [
    rds.ClusterInstance.provisioned('reader', {
      instanceType: ec2.InstanceType.of(
        ec2.InstanceClass.T4G,
        ec2.InstanceSize.MEDIUM
      )
    })
  ],
  vpc,
  vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED }
});
```

---

### フェーズ5: コンピューティング基盤（優先度：最高）

#### 5.1 ECRリポジトリの作成
**目的**: コンテナイメージの管理

**実装内容**:
- バックエンドAPI用ECRリポジトリ
- イメージスキャン: プッシュ時の自動スキャン有効
- イメージタグの変更可能性: 有効（MUTABLE）
- ライフサイクルポリシー: 最新10イメージを保持、それ以外は自動削除
- 暗号化: AES-256

**成果物**:
- `cdk/lib/stacks/compute-stack.ts`

**依存関係**: 1.2

**参考CDKリソース**:
```typescript
import * as ecr from 'aws-cdk-lib/aws-ecr';

const repository = new ecr.Repository(this, 'BackendRepository', {
  imageScanOnPush: true,
  lifecycleRules: [
    {
      maxImageCount: 10,
      description: 'Keep last 10 images'
    }
  ]
});
```

---

#### 5.2 Application Load Balancerの構築
**目的**: ECSサービスへのトラフィック分散

**実装内容**:
- ALBの作成（インターネット向け）
- パブリックサブネット（マルチAZ）への配置
- セキュリティグループ
  - インバウンド: HTTPS (443)、HTTP (80) from 0.0.0.0/0
  - アウトバウンド: ECSセキュリティグループへ
- ターゲットグループの作成
  - ターゲットタイプ: IP（Fargate用）
  - プロトコル: HTTP (ポート8000)
  - ヘルスチェック: /health、間隔30秒、タイムアウト5秒
- HTTPSリスナー（ACM証明書を使用）
- HTTP → HTTPSリダイレクト設定
- アクセスログのS3保存
- WAFの関連付け（フェーズ3.3で作成したWeb ACL）
- Route 53 Aレコードの作成（api.example.com → ALB）

**成果物**:
- `cdk/lib/constructs/alb-with-waf.ts`
- `cdk/lib/stacks/compute-stack.ts`（一部）

**依存関係**: 2.1（VPC）、2.2（Route 53）、3.3（WAF）

**注意**:
- ACM証明書は事前に作成（DNS検証完了済み）、またはCDKで作成
- S3バケット（ALBログ用）はフェーズ6で作成

**参考CDKリソース**:
```typescript
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';

const alb = new elbv2.ApplicationLoadBalancer(this, 'ALB', {
  vpc,
  internetFacing: true,
  vpcSubnets: { subnetType: ec2.SubnetType.PUBLIC }
});

const certificate = acm.Certificate.fromCertificateArn(
  this,
  'Certificate',
  certificateArn
);

const httpsListener = alb.addListener('HttpsListener', {
  port: 443,
  certificates: [certificate]
});
```

---

#### 5.3 ECS Clusterの作成
**目的**: Fargateタスク実行基盤

**実装内容**:
- ECS Clusterの作成
- Container Insightsの有効化

**成果物**:
- `cdk/lib/stacks/compute-stack.ts`（一部）

**依存関係**: 2.1（VPC）

**参考CDKリソース**:
```typescript
import * as ecs from 'aws-cdk-lib/aws-ecs';

const cluster = new ecs.Cluster(this, 'Cluster', {
  vpc,
  containerInsights: true
});
```

---

#### 5.4 ECS Fargate Service（FastAPI + Fluent Bit）の実装
**目的**: バックエンドAPIのデプロイとログ収集

**実装内容**:
- ECSタスク定義の作成
  - Fargate起動タイプ
  - CPU、メモリ: 環境設定から取得
    - 開発: CPU 512 (0.5 vCPU)、メモリ 1024 MB
    - 本番: CPU 1024 (1 vCPU)、メモリ 2048 MB
  - **メインコンテナ（FastAPI）**:
    - ECRイメージ参照
    - ポート8000公開
    - 環境変数（Aurora接続情報はSecrets Managerから取得）
    - ログ設定: FireLens経由でFluent Bitへ
  - **サイドカーコンテナ（Fluent Bit）**:
    - イメージ: amazon/aws-for-fluent-bit:latest
    - FireLens設定
    - Fluent Bit設定ファイル（S3またはインライン）
      - ERRORレベル以上 → CloudWatch Logs
      - 全ログ → S3バケット
- ECSサービスの作成
  - プライベートサブネットへの配置
  - 希望タスク数: 2（マルチAZ構成）
  - デプロイ設定: ローリングアップデート
  - セキュリティグループ
    - インバウンド: ALBからのアクセス（ポート8000）
    - アウトバウンド: Auroraへの接続（ポート5432）、HTTPS（443）
  - ALBターゲットグループへの登録
- タスク実行ロール
  - ECRイメージプル権限
  - Secrets Manager読み取り権限
  - CloudWatch Logs書き込み権限
- タスクロール
  - S3書き込み権限（ログバケット）
  - Auroraアクセス権限（必要に応じて）
- Service Auto Scalingの設定
  - CPU使用率ベースのスケーリング（70%で追加）
  - 最小タスク数: 2、最大タスク数: 10

**成果物**:
- `cdk/lib/constructs/ecs-fargate-service.ts`
- `cdk/lib/stacks/compute-stack.ts`（一部）

**依存関係**: 4.1（Aurora）、5.1（ECR）、5.2（ALB）、5.3（ECS Cluster）

**Fluent Bit設定例**:
```conf
[FILTER]
    Name    grep
    Match   app-firelogs-*
    Regex   level (ERROR|CRITICAL|FATAL)

[OUTPUT]
    Name    cloudwatch_logs
    Match   app-firelogs-*
    region  ap-northeast-1
    log_group_name  /ecs/backend/errors
    log_stream_prefix  fargate-

[OUTPUT]
    Name    s3
    Match   app-firelogs-*
    region  ap-northeast-1
    bucket  ${LOG_BUCKET_NAME}
    total_file_size  100M
    upload_timeout  10m
    s3_key_format  /year=%Y/month=%m/day=%d/hour=%H/$UUID.gz
    compression  gzip
```

**参考CDKリソース**:
```typescript
import * as ecs from 'aws-cdk-lib/aws-ecs';

const taskDefinition = new ecs.FargateTaskDefinition(this, 'TaskDef', {
  cpu: 512,
  memoryLimitMiB: 1024
});

const appContainer = taskDefinition.addContainer('app', {
  image: ecs.ContainerImage.fromEcrRepository(repository),
  logging: ecs.LogDrivers.firelens({
    options: {
      Name: 'forward',
      Host: 'log-router',
      Port: '24224'
    }
  })
});

const logRouter = taskDefinition.addFirelensLogRouter('log-router', {
  image: ecs.ContainerImage.fromRegistry('amazon/aws-for-fluent-bit:latest'),
  firelensConfig: {
    type: ecs.FirelensLogRouterType.FLUENTBIT
  }
});
```

---

### フェーズ6: 監視とロギング基盤（優先度：中）

#### 6.1 S3バケット（ログ保存用）の作成
**目的**: 全レベルログの長期保存とALBアクセスログの保存

**実装内容**:
- **アプリケーションログバケット**（Fluent Bit → S3）
  - バケットポリシー（ECSタスクロールからのアクセス許可）
  - ライフサイクルポリシー
    - 90日後: Glacier Flexible Retrievalへ移行
    - 1年後: 削除
  - バージョニング有効化
  - 暗号化（SSE-S3）
  - パブリックアクセスブロック
- **ALBアクセスログバケット**
  - バケットポリシー（ALBサービスからのアクセス許可）
  - ライフサイクルポリシー（同上）
  - 暗号化、パブリックアクセスブロック

**成果物**:
- `cdk/lib/stacks/monitoring-stack.ts`

**依存関係**: 1.2

**参考CDKリソース**:
```typescript
import * as s3 from 'aws-cdk-lib/aws-s3';

const logBucket = new s3.Bucket(this, 'LogBucket', {
  encryption: s3.BucketEncryption.S3_MANAGED,
  blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
  versioned: true,
  lifecycleRules: [
    {
      transitions: [
        {
          storageClass: s3.StorageClass.GLACIER,
          transitionAfter: cdk.Duration.days(90)
        }
      ],
      expiration: cdk.Duration.days(365)
    }
  ]
});
```

---

#### 6.2 CloudWatch Logs設定
**目的**: ERRORレベル以上のログ収集

**実装内容**:
- ロググループの作成
  - `/ecs/backend/errors`: ECSコンテナERRORログ用
  - `/aws/vpc/flowlogs`: VPCフローログ用
- ログ保持期間の設定
  - 開発: 7日
  - 本番: 30日

**成果物**:
- `cdk/lib/stacks/monitoring-stack.ts`（一部）

**依存関係**: なし（各スタックで個別作成も可）

**参考CDKリソース**:
```typescript
import * as logs from 'aws-cdk-lib/aws-logs';

new logs.LogGroup(this, 'ErrorLogGroup', {
  logGroupName: '/ecs/backend/errors',
  retention: logs.RetentionDays.ONE_WEEK
});
```

---

#### 6.3 CloudWatch Alarmsの作成
**目的**: システム異常の検知と通知

**実装内容**:
- **ECS関連アラーム**:
  - ERRORログ検出（メトリクスフィルタ使用）
  - CPU使用率 > 80%（5分間継続）
  - メモリ使用率 > 80%（5分間継続）
  - タスク起動失敗
- **Aurora関連アラーム**:
  - CPU使用率 > 80%
  - ディスク使用率 > 85%
  - 接続数 > 閾値（インスタンスクラスに応じて）
  - レプリカラグ > 1秒
- **ALB関連アラーム**:
  - 5xxエラー率 > 5%（5分間）
  - ターゲットヘルスチェック失敗
  - レスポンスタイム > 2秒
- **アクション**: SNSトピックへ通知

**成果物**:
- `cdk/lib/stacks/monitoring-stack.ts`（一部）

**依存関係**: 4.1（Aurora）、5.2（ALB）、5.4（ECS）、6.4（SNS）

**参考CDKリソース**:
```typescript
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as actions from 'aws-cdk-lib/aws-cloudwatch-actions';

const errorMetricFilter = new logs.MetricFilter(this, 'ErrorMetric', {
  logGroup,
  metricNamespace: 'App/Errors',
  metricName: 'ErrorCount',
  filterPattern: logs.FilterPattern.stringValue('$.level', '=', 'ERROR')
});

const alarm = new cloudwatch.Alarm(this, 'ErrorAlarm', {
  metric: errorMetricFilter.metric(),
  threshold: 5,
  evaluationPeriods: 1
});

alarm.addAlarmAction(new actions.SnsAction(snsTopic));
```

---

#### 6.4 Amazon SNSトピックの作成
**目的**: アラート通知の配信

**実装内容**:
- **critical-alerts**: 本番環境のクリティカルアラート
  - メール通知
  - Slack通知（オプション、Lambda統合）
- **warning-alerts**: 警告レベルのアラート
  - メール通知
- サブスクリプションの作成（メールアドレス）

**成果物**:
- `cdk/lib/stacks/monitoring-stack.ts`（一部）

**依存関係**: 1.2

**参考CDKリソース**:
```typescript
import * as sns from 'aws-cdk-lib/aws-sns';
import * as subscriptions from 'aws-cdk-lib/aws-sns-subscriptions';

const criticalTopic = new sns.Topic(this, 'CriticalAlerts', {
  displayName: 'Critical Alerts'
});

criticalTopic.addSubscription(
  new subscriptions.EmailSubscription('admin@example.com')
);
```

---

#### 6.5 CloudWatch Dashboardの作成
**目的**: システム全体の監視ダッシュボード

**実装内容**:
- **ECS メトリクス**:
  - CPU、メモリ使用率
  - タスク数
  - エラーログ数
- **Aurora メトリクス**:
  - CPU使用率
  - 接続数
  - レプリカラグ
- **ALB メトリクス**:
  - リクエスト数
  - レイテンシ
  - エラー率（4xx、5xx）
- **VPCエンドポイント データ転送量**
- ウィジェットの配置

**成果物**:
- `cdk/lib/stacks/monitoring-stack.ts`（一部）

**依存関係**: 5.4（ECS）、4.1（Aurora）、5.2（ALB）

**参考CDKリソース**:
```typescript
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';

const dashboard = new cloudwatch.Dashboard(this, 'Dashboard', {
  dashboardName: 'ApplicationDashboard'
});

dashboard.addWidgets(
  new cloudwatch.GraphWidget({
    title: 'ECS CPU Utilization',
    left: [service.metricCpuUtilization()]
  })
);
```

---

### フェーズ7: CI/CD統合（優先度：中）

#### 7.1 GitHub Actions用IAMロールの作成
**目的**: GitHub ActionsからのECSデプロイを許可

**実装内容**:
- OIDC Providerの作成（GitHub Actions用）
  - URL: `https://token.actions.githubusercontent.com`
  - Audience: `sts.amazonaws.com`
- IAMロールの作成
  - ECRへのプッシュ権限（ecr:PutImage、ecr:InitiateLayerUpload等）
  - ECSタスク定義の登録権限（ecs:RegisterTaskDefinition）
  - ECSサービスの更新権限（ecs:UpdateService）
- 信頼ポリシーの設定（GitHubリポジトリとブランチを制限）
  - リポジトリ: `repo:organization/repository:*`
  - ブランチ: `ref:refs/heads/main`、`ref:refs/heads/develop`

**成果物**:
- `cdk/lib/stacks/compute-stack.ts`（一部）

**依存関係**: 5.1（ECR）、5.4（ECS Service）

**参考CDKリソース**:
```typescript
import * as iam from 'aws-cdk-lib/aws-iam';

const githubProvider = new iam.OpenIdConnectProvider(this, 'GithubProvider', {
  url: 'https://token.actions.githubusercontent.com',
  clientIds: ['sts.amazonaws.com']
});

const githubRole = new iam.Role(this, 'GithubActionsRole', {
  assumedBy: new iam.FederatedPrincipal(
    githubProvider.openIdConnectProviderArn,
    {
      StringLike: {
        'token.actions.githubusercontent.com:sub': 'repo:org/repo:*'
      }
    },
    'sts:AssumeRoleWithWebIdentity'
  )
});
```

---

### フェーズ8: オプション機能（優先度：低 - 後回し）

#### 8.1 Amazon Athenaの設定（オプション）
**目的**: S3ログのクエリと分析

**実装内容**:
- Glue Data Catalogデータベースの作成
- Glueテーブルの作成（S3ログバケットのパーティション構造に対応）
- Athena Workgroupの作成
- クエリ結果保存用S3バケット

**成果物**:
- `cdk/lib/stacks/monitoring-stack.ts`（一部）

**依存関係**: 6.1（S3ログバケット）

---

#### 8.2 EventBridgeルールの作成（将来実装）
**目的**: スケジュールベースまたはイベントベースのトリガー

**実装内容**:
- EventBridgeルールの作成（スケジュール実行やイベントパターン）
- Step Functionsステートマシンへのターゲット設定

**成果物**:
- `cdk/lib/stacks/orchestration-stack.ts`

**依存関係**: 8.3（Step Functions）

---

#### 8.3 Step Functionsステートマシンの作成（将来実装）
**目的**: ワークフローの制御

**実装内容**:
- ステートマシンの定義（サンプルワークフロー）
- ECSタスク起動の統合
- エラーハンドリングとリトライ設定
- CloudWatch Logsへのログ出力

**成果物**:
- `cdk/lib/stacks/orchestration-stack.ts`（一部）

**依存関係**: 5.4（ECS Service）

---

#### 8.4 AWS Amplifyの構築（将来実装）
**目的**: Next.jsフロントエンドのホスティング

**実装内容**:
- Amplify Appの作成
- GitHubリポジトリとの連携
- ビルド設定（amplify.yml）
- 環境変数の設定（バックエンドAPIのURL等）
- カスタムドメインの設定（Route53と連携）
- 基本認証の設定（dev環境のみ、オプション）

**成果物**:
- `cdk/lib/stacks/frontend-stack.ts`

**依存関係**: 5.2（ALB - バックエンドAPIのURL）

---

## スタック間の依存関係

```
[フェーズ1] 基盤
    ↓
[フェーズ2] NetworkStack (VPC, Route53)
    ↓
[フェーズ3] SecurityStack (GuardDuty, Config, WAF)
    ↓
[フェーズ4] DatabaseStack (Aurora) ← NetworkStack
    ↓
[フェーズ5] ComputeStack (ECR, ALB+WAF, ECS+Fluent Bit) ← NetworkStack, SecurityStack, DatabaseStack
    ↓
[フェーズ6] MonitoringStack (S3, CloudWatch, SNS) ← ComputeStack, DatabaseStack
    ↓
[フェーズ7] CI/CD (GitHub Actions Role) ← ComputeStack
```

## CDKアプリケーションエントリーポイント例

`cdk/bin/app.ts`:
```typescript
#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { NetworkStack } from '../lib/stacks/network-stack';
import { SecurityStack } from '../lib/stacks/security-stack';
import { DatabaseStack } from '../lib/stacks/database-stack';
import { ComputeStack } from '../lib/stacks/compute-stack';
import { MonitoringStack } from '../lib/stacks/monitoring-stack';
import { getEnvConfig } from '../lib/config/env-config';

const app = new cdk.App();

const envName = app.node.tryGetContext('env') || 'dev';
const config = getEnvConfig(envName);

const env = {
  account: process.env.CDK_DEFAULT_ACCOUNT,
  region: config.region
};

const networkStack = new NetworkStack(app, `NetworkStack-${envName}`, {
  env,
  config
});

const securityStack = new SecurityStack(app, `SecurityStack-${envName}`, {
  env,
  config
});

const databaseStack = new DatabaseStack(app, `DatabaseStack-${envName}`, {
  env,
  config,
  vpc: networkStack.vpc
});

const computeStack = new ComputeStack(app, `ComputeStack-${envName}`, {
  env,
  config,
  vpc: networkStack.vpc,
  database: databaseStack.cluster,
  webAcl: securityStack.webAcl
});

const monitoringStack = new MonitoringStack(app, `MonitoringStack-${envName}`, {
  env,
  config,
  ecsService: computeStack.service,
  alb: computeStack.alb,
  database: databaseStack.cluster
});

app.synth();
```

## デプロイコマンド

### 事前準備
```bash
# CDKのインストール
npm install -g aws-cdk

# AWSアカウントのブートストラップ
cdk bootstrap aws://ACCOUNT_ID/ap-northeast-1

# 依存関係のインストール
cd cdk
npm install
```

### 開発環境
```bash
# すべてのスタックをデプロイ
cdk deploy --all --context env=dev

# 個別スタックのデプロイ（依存関係順）
cdk deploy NetworkStack-dev --context env=dev
cdk deploy SecurityStack-dev --context env=dev
cdk deploy DatabaseStack-dev --context env=dev
cdk deploy ComputeStack-dev --context env=dev
cdk deploy MonitoringStack-dev --context env=dev

# 差分確認
cdk diff --all --context env=dev
```

### 本番環境
```bash
# すべてのスタックをデプロイ（承認が必要な変更がある場合は確認）
cdk deploy --all --context env=prod --require-approval broadening

# 個別スタックのデプロイ
cdk deploy NetworkStack-prod --context env=prod
cdk deploy SecurityStack-prod --context env=prod
cdk deploy DatabaseStack-prod --context env=prod
cdk deploy ComputeStack-prod --context env=prod
cdk deploy MonitoringStack-prod --context env=prod
```

## 環境設定パラメータ例

### 開発環境（dev）
```typescript
export const devConfig: EnvConfig = {
  envName: 'dev',
  region: 'ap-northeast-1',
  vpcCidr: '10.0.0.0/16',
  availabilityZones: ['ap-northeast-1a', 'ap-northeast-1c'],
  publicSubnetCidrs: ['10.0.1.0/24', '10.0.2.0/24'],
  privateSubnetCidrs: ['10.0.11.0/24', '10.0.12.0/24'],
  useVpcEndpoints: true, // VPCエンドポイントを使用（NAT Gatewayの代替）
  ecs: {
    cpu: 512,
    memory: 1024,
    desiredCount: 2,
    minCapacity: 2,
    maxCapacity: 10
  },
  aurora: {
    instanceClass: 'db.t4g.medium',
    backupRetentionDays: 7,
    deletionProtection: false
  },
  logRetentionDays: 7,
  domainName: 'dev-api.example.com'
};
```

### 本番環境（prod）
```typescript
export const prodConfig: EnvConfig = {
  envName: 'prod',
  region: 'ap-northeast-1',
  vpcCidr: '10.1.0.0/16',
  availabilityZones: ['ap-northeast-1a', 'ap-northeast-1c'],
  publicSubnetCidrs: ['10.1.1.0/24', '10.1.2.0/24'],
  privateSubnetCidrs: ['10.1.11.0/24', '10.1.12.0/24'],
  useVpcEndpoints: true, // VPCエンドポイントを使用（NAT Gatewayの代替）
  ecs: {
    cpu: 1024,
    memory: 2048,
    desiredCount: 2,
    minCapacity: 2,
    maxCapacity: 20
  },
  aurora: {
    instanceClass: 'db.r6g.large',
    backupRetentionDays: 30,
    deletionProtection: true
  },
  logRetentionDays: 30,
  domainName: 'api.example.com'
};
```

## コスト最適化のポイント

1. **VPCエンドポイント（NAT Gatewayの代替）**:
   - NAT Gateway方式: 約$64/月（2個 × $32） + データ転送料
   - VPCエンドポイント方式: 約$28.8/月（Interface型 × 4個） + $0（Gateway型）
   - **削減額**: 約$35/月（年間約$420）
   - 対象サービス: S3（Gateway型、無料）、ECR、Secrets Manager、CloudWatch Logs（Interface型）

2. **ログ保存**:
   - ERRORログのみCloudWatch Logs（大幅コスト削減）
   - 全ログはS3に保存（約85%削減）
   - 例: 月間100GBのログで約$45削減

3. **Aurora**:
   - 開発環境: t4g.medium（約$60/月）
   - 本番環境: r6g.large（約$250/月）

4. **ECS Fargate**:
   - 開発環境: CPU 512、Memory 1024（約$35/月 × タスク数）
   - 本番環境: CPU 1024、Memory 2048（約$70/月 × タスク数）

5. **S3ライフサイクル**:
   - 90日後Glacier移行（約90%削減）
   - 1年後削除

6. **CloudWatch Logs保持期間**:
   - 開発: 7日、本番: 30日

## セキュリティベストプラクティス

1. **最小権限の原則**: IAMロールは必要最小限の権限のみ付与
2. **暗号化**: すべてのデータ（保管時・転送時）を暗号化
3. **ネットワーク分離**: パブリック/プライベートサブネットの適切な分離
4. **セキュリティグループ**: 必要最小限のポート・ソースのみ許可
5. **シークレット管理**: Secrets Managerを使用し、コード内にハードコーディングしない
6. **削除保護**: 本番環境のAuroraには削除保護を有効化
7. **監査ログ**: CloudTrail、VPCフローログ、ALBアクセスログを有効化
8. **イメージスキャン**: ECRプッシュ時の自動スキャン
9. **WAF**: マネージドルールセットによるWeb攻撃対策

## 注意事項

1. **ドメイン**: カスタムドメインは事前に取得・Route53に登録が必要
2. **GitHub連携**: GitHub Actionsの連携にはPersonal Access Tokenまたはアプリの設定が必要
3. **ACM証明書**: DNS検証が必要（CDKで自動化可能だが、初回は時間がかかる）
4. **初回デプロイ**: ECRにイメージがない場合、ECSサービスは起動失敗する
   - 対策: ECRにダミーイメージを先にプッシュ、またはCI/CDで最初のイメージをプッシュ後にサービス起動
5. **コスト**: NAT Gateway、Fargate、Auroraは継続的なコストが発生
6. **削除時**:
   - Auroraスナップショット、S3バケットは手動削除が必要な場合あり
   - `cdk destroy`前にリソースの削除保護を無効化

## 実装時のチェックリスト

### 事前準備
- [ ] AWS CLIとCDK CLIのインストール・設定
- [ ] AWSアカウントのブートストラップ（`cdk bootstrap`）
- [ ] ドメインの取得とRoute53への登録
- [ ] GitHub Personal Access Tokenの発行（CI/CD用）
- [ ] 環境設定ファイル（dev.ts、prod.ts）の値を確認・調整

### フェーズ1-2: 基盤・ネットワーク
- [ ] CDKプロジェクトの初期化
- [ ] 環境設定ファイルの作成
- [ ] NetworkStackのデプロイ
- [ ] VPC、サブネットの作成確認
- [ ] Route 53 Hosted Zoneの設定

### フェーズ3: セキュリティ
- [ ] SecurityStackのデプロイ
- [ ] GuardDutyの有効化確認
- [ ] AWS Configの設定確認
- [ ] WAF Web ACLの作成確認

### フェーズ4: データベース
- [ ] DatabaseStackのデプロイ
- [ ] Auroraクラスターの作成確認
- [ ] プライマリ・レプリカインスタンスの起動確認
- [ ] Secrets Managerの認証情報確認

### フェーズ5: コンピューティング
- [ ] ECRリポジトリの作成
- [ ] バックエンドDockerイメージのビルドとECRへのプッシュ
- [ ] ACM証明書の作成・DNS検証完了
- [ ] ComputeStackのデプロイ
- [ ] ALBの作成確認
- [ ] ECS Clusterの作成確認
- [ ] ECSタスク定義の登録確認（FastAPI + Fluent Bit）
- [ ] ECSサービスの起動確認（タスク数2）
- [ ] ALBヘルスチェックの確認
- [ ] Route 53 AレコードのALBへの紐付け確認

### フェーズ6: 監視・ロギング
- [ ] MonitoringStackのデプロイ
- [ ] S3ログバケットの作成確認
- [ ] CloudWatch Logsロググループの作成確認
- [ ] Fluent Bitからのログ送信確認（CloudWatch + S3）
- [ ] CloudWatch Alarmsの作成確認
- [ ] SNSトピック・サブスクリプションの作成確認
- [ ] テストアラートの送信・受信確認
- [ ] CloudWatch Dashboardの表示確認

### フェーズ7: CI/CD
- [ ] GitHub Actions用IAMロールの作成
- [ ] GitHub ActionsワークフローファイルのCI/CD設定
- [ ] プッシュ時の自動デプロイテスト

### 最終確認
- [ ] E2Eテスト（フロントエンド → ALB → ECS → Aurora）
- [ ] エラーログのCloudWatch Logs送信確認
- [ ] 全ログのS3保存確認
- [ ] Auto Scalingの動作確認（負荷テスト）
- [ ] フェイルオーバーテスト（AZ障害想定）
- [ ] コスト確認（AWS Cost Explorer）

## トラブルシューティング

### ECSタスクが起動しない
- ECRイメージが存在するか確認
- タスク実行ロールの権限確認（ECR、Secrets Manager）
- セキュリティグループの設定確認
- CloudWatch Logsでタスク起動ログを確認

### ALBヘルスチェックが失敗する
- ECSタスクの/healthエンドポイントが正常に応答するか確認
- セキュリティグループでALB → ECS（ポート8000）が許可されているか確認
- ターゲットグループのヘルスチェック設定を確認

### Fluent BitからCloudWatch Logsに送信されない
- タスクロールにCloudWatch Logs書き込み権限があるか確認
- Fluent Bit設定ファイルの構文確認
- Fluent Bitコンテナのログを確認

### データベース接続エラー
- Secrets Managerの認証情報が正しいか確認
- セキュリティグループでECS → Aurora（ポート5432）が許可されているか確認
- Auroraエンドポイントが正しいか確認

## 次のステップ

1. **パフォーマンス最適化**: CloudFront、ElastiCacheの追加検討
2. **バックアップ戦略**: Auroraスナップショットの自動化、リストア手順の文書化
3. **災害復旧**: マルチリージョン構成の検討
4. **Step Functions/EventBridge**: バッチ処理やワークフロー機能の追加
5. **AWS Amplify**: フロントエンド基盤の追加
6. **モニタリング強化**: X-Rayによる分散トレーシング

## 更新履歴
- 2026-01-22: 初版作成、NAT GatewayをVPCエンドポイントに変更（コスト最適化: 年間約$420削減）

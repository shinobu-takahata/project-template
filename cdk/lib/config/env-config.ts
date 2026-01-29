import { devConfig } from './dev';
import { prodConfig } from './prod';

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

  // 削除ポリシー設定
  removalPolicy: {
    s3Buckets: 'RETAIN' | 'DESTROY';
    logGroups: 'RETAIN' | 'DESTROY';
    database: 'RETAIN' | 'SNAPSHOT' | 'DESTROY';
    ecrRepositories: 'RETAIN' | 'DESTROY';
  };

  // GitHub Actions CI/CD設定
  github?: {
    owner: string;           // GitHubオーナー（組織またはユーザー）
    repository: string;      // リポジトリ名
    branches: string[];      // 許可するブランチ（例: ['main', 'develop']）
  };

  // 監視設定
  monitoring?: {
    // アラート通知先メールアドレス
    alertEmail?: string;

    // アラーム閾値
    thresholds?: {
      // ECS関連
      errorLogCount?: number;              // デフォルト: 5
      ecsCpuPercent?: number;              // デフォルト: 80
      ecsMemoryPercent?: number;           // デフォルト: 80

      // Aurora関連
      auroraCpuPercent?: number;           // デフォルト: 80
      auroraFreeableMemoryBytes?: number;  // デフォルト: 1GB (1_000_000_000)
      auroraConnectionsCount?: number;     // デフォルト: 80
      auroraReplicaLagMs?: number;         // デフォルト: 1000 (1秒)

      // ALB関連
      alb5xxErrorRatePercent?: number;     // デフォルト: 5
      albResponseTimeSeconds?: number;     // デフォルト: 2
    };
  };

  // オーケストレーション設定（Step Functions + EventBridge）
  orchestration?: {
    // スケジュール実行の有効/無効
    enabled: boolean;

    // EventBridgeスケジュール式（cron式、UTC）
    // 例: 'cron(0 17 * * ? *)' = JST午前2時
    scheduleExpression: string;

    // バッチスクリプトのパス（コンテナ内）
    batchScriptPath: string;
  };
}

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

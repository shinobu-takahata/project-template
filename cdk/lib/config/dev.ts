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
    desiredCount: 0,    // TODO: イメージプッシュ後に2に変更
    minCapacity: 0,     // TODO: イメージプッシュ後に2に変更
    maxCapacity: 10
  },

  // Aurora設定（開発環境はt3.medium - Aurora PostgreSQLサポート）
  aurora: {
    instanceClass: 'db.t3.medium',
    backupRetentionDays: 7,
    deletionProtection: false  // 開発環境は削除保護なし
  },

  // ログ設定（開発環境は短期保持）
  logRetentionDays: 7,

  // ドメイン設定
  domainName: 'dev-api.example.com',

  // 削除ポリシー設定（開発環境は完全削除可能）
  removalPolicy: {
    s3Buckets: 'DESTROY',   // S3バケットも削除
    logGroups: 'DESTROY',    // ロググループも削除
    database: 'DESTROY'      // DBも完全削除（スナップショット不要）
  }
};

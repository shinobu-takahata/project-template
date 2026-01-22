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

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

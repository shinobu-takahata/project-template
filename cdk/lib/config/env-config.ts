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

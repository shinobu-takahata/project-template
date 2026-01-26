#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { NetworkStack } from '../lib/stacks/network-stack';
import { SecurityStack } from '../lib/stacks/security-stack';
import { DatabaseStack } from '../lib/stacks/database-stack';
import { ComputeStack } from '../lib/stacks/compute-stack';
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

// NetworkStackの作成
const networkStack = new NetworkStack(app, `NetworkStack-${envName}`, {
  env,
  config
});

// SecurityStackの作成
const securityStack = new SecurityStack(app, `SecurityStack-${envName}`, {
  env,
  config
});

// DatabaseStackの作成
const databaseStack = new DatabaseStack(app, `DatabaseStack-${envName}`, {
  env,
  config
});

// ComputeStackの作成
const computeStack = new ComputeStack(app, `ComputeStack-${envName}`, {
  env,
  config
});

// 依存関係を設定
computeStack.addDependency(networkStack);
computeStack.addDependency(securityStack);
computeStack.addDependency(databaseStack);

// CDKアプリケーションの合成
app.synth();

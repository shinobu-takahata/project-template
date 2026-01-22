#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
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

// スタック作成の準備（フェーズ2以降で実装）
// 例:
// const networkStack = new NetworkStack(app, `NetworkStack-${envName}`, {
//   env,
//   config
// });

// CDKアプリケーションの合成
app.synth();

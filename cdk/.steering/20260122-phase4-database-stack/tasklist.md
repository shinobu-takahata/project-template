# フェーズ4: データベース基盤 - タスクリスト

## 概要
DatabaseStackの実装タスクを管理します。

## タスク一覧

### 1. DatabaseStackファイルの作成
- [ ] **1.1** `lib/stacks/database-stack.ts`の作成
- [ ] **1.2** 必要なインポートの追加
  - aws-cdk-lib（Stack, StackProps, RemovalPolicy, CfnOutput, Fn, Duration, Tags）
  - aws-cdk-lib/aws-rds
  - aws-cdk-lib/aws-ec2
  - aws-cdk-lib/aws-secretsmanager
  - aws-cdk-lib/aws-logs
  - constructs
  - ../config/env-config
- [ ] **1.3** DatabaseStackPropsインターフェースの定義
- [ ] **1.4** DatabaseStackクラスの定義

**完了条件**: DatabaseStackの基本構造が作成されていること

---

### 2. VPCのインポート
- [ ] **2.1** NetworkStackからVPC IDをインポート
  - `Fn.importValue(\`${config.envName}-VpcId\`)`
- [ ] **2.2** プライベートサブネットIDをインポート
  - `Fn.importValue(\`${config.envName}-PrivateSubnetId1\`)`
  - `Fn.importValue(\`${config.envName}-PrivateSubnetId2\`)`
- [ ] **2.3** `Vpc.fromVpcAttributes`でVPCオブジェクトを構築

**完了条件**: VPCとサブネットが正しくインポートされていること

---

### 3. Secrets Manager（データベース認証情報）の実装
- [ ] **3.1** Secrets Managerリソースの作成
  - シークレット名: `${config.envName}/aurora/credentials`
  - ユーザー名: `dbadmin`
  - パスワード: 自動生成（32文字）
  - 除外文字: `"@/\`
  - 削除ポリシー: 環境設定に従う
- [ ] **3.2** タグ付け
  - Environment: config.envName
  - Project: project-template
  - ManagedBy: CDK

**完了条件**: Secrets Managerが正しく設定されていること

---

### 4. DBサブネットグループの実装
- [ ] **4.1** CfnDBSubnetGroupリソースの作成
  - dbSubnetGroupName: `db-subnet-group-${config.envName}`
  - subnetIds: インポートしたプライベートサブネット2つ
- [ ] **4.2** タグ付け

**完了条件**: DBサブネットグループが正しく作成されていること

---

### 5. DBセキュリティグループの実装
- [ ] **5.1** SecurityGroupリソースの作成
  - securityGroupName: `db-sg-${config.envName}`
  - description: 'Security group for Aurora database'
  - allowAllOutbound: true
- [ ] **5.2** インバウンドルールの追加
  - ポート: 5432（PostgreSQL）
  - 送信元: VPC CIDR（`config.vpcCidr`）
  - 説明: 'Allow PostgreSQL access from VPC'
- [ ] **5.3** タグ付け

**完了条件**: DBセキュリティグループが正しく作成されていること

---

### 6. Aurora PostgreSQL Clusterの実装

#### 6.1 基本設定
- [ ] **6.1.1** DatabaseClusterリソースの作成
  - engine: Aurora PostgreSQL 15.4
  - credentials: Secrets Managerから取得
  - vpc: インポートしたVPC
  - vpcSubnets: プライベートサブネット
  - securityGroups: DBセキュリティグループ

#### 6.2 Writer Instance（Primary）の設定
- [ ] **6.2.1** ClusterInstance.provisionedでWriterを作成
  - instanceType: 環境設定から取得（dev: db.t4g.small、prod: db.r6g.large）
  - availabilityZone: config.availabilityZones[0]（AZ-1）
  - enablePerformanceInsights: 本番環境のみ有効
  - performanceInsightRetention: 本番環境のみ7日間

#### 6.3 Reader Instance（Replica）の設定
- [ ] **6.3.1** ClusterInstance.provisionedでReaderを作成
  - instanceType: Writerと同じ
  - availabilityZone: config.availabilityZones[1]（AZ-2）
  - enablePerformanceInsights: 本番環境のみ有効
  - performanceInsightRetention: 本番環境のみ7日間

#### 6.4 バックアップ設定
- [ ] **6.4.1** バックアップ設定の追加
  - retention: 環境設定に従う（dev: 7日、prod: 30日）
  - preferredWindow: '03:00-04:00'（UTC）

#### 6.5 メンテナンス設定
- [ ] **6.5.1** メンテナンスウィンドウの設定
  - preferredMaintenanceWindow: 'sun:19:00-sun:20:00'（UTC）

#### 6.6 セキュリティ設定
- [ ] **6.6.1** 暗号化の有効化
  - storageEncrypted: true
- [ ] **6.6.2** 削除保護の設定
  - deletionProtection: 環境設定に従う（dev: false、prod: true）
- [ ] **6.6.3** 削除ポリシーの設定
  - removalPolicy: 環境設定に従う（dev: DESTROY、prod: SNAPSHOT）

#### 6.7 ログ設定
- [ ] **6.7.1** CloudWatch Logsエクスポートの設定
  - cloudwatchLogsExports: ['postgresql']
  - cloudwatchLogsRetention: 環境設定に従う（dev: 7日、prod: 30日）

#### 6.8 タグ付け
- [ ] **6.8.1** タグ付け
  - Environment: config.envName
  - Project: project-template
  - ManagedBy: CDK

**完了条件**: Aurora PostgreSQL Clusterが正しく設定されていること

---

### 7. エクスポート（CfnOutput）の実装
- [ ] **7.1** DBクラスタARNのエクスポート
  - exportName: `${config.envName}-DbClusterArn`
- [ ] **7.2** DBクラスタエンドポイント（書き込み用）のエクスポート
  - exportName: `${config.envName}-DbClusterEndpoint`
- [ ] **7.3** DBクラスタ読み取りエンドポイントのエクスポート
  - exportName: `${config.envName}-DbClusterReadEndpoint`
- [ ] **7.4** DBシークレットARNのエクスポート
  - exportName: `${config.envName}-DbSecretArn`
- [ ] **7.5** DBセキュリティグループIDのエクスポート
  - exportName: `${config.envName}-DbSecurityGroupId`

**完了条件**: すべてのエクスポートが設定されていること

---

### 8. エントリーポイントの更新
- [ ] **8.1** `bin/app.ts`を開く
- [ ] **8.2** DatabaseStackのインポート追加
  ```typescript
  import { DatabaseStack } from '../lib/stacks/database-stack';
  ```
- [ ] **8.3** DatabaseStackの作成追加（NetworkStackの後）
  ```typescript
  const databaseStack = new DatabaseStack(app, `DatabaseStack-${envName}`, {
    env,
    config
  });
  ```

**完了条件**: bin/app.tsが更新され、DatabaseStackが作成されること

---

### 9. ビルドと検証

#### 9.1 TypeScriptコンパイル
- [ ] **9.1.1** npm run buildの実行
  ```bash
  npm run build
  ```
- [ ] **9.1.2** コンパイル成功の確認
  - `lib/stacks/database-stack.js`が生成されていること
  - エラーが出ていないこと

**完了条件**: TypeScriptのコンパイルが正常に完了すること

#### 9.2 CDK合成テスト（dev環境）
- [ ] **9.2.1** AWS_PROFILEとAWS_REGIONを設定
  ```bash
  export AWS_PROFILE=takahata
  export AWS_REGION=ap-northeast-1
  ```
- [ ] **9.2.2** cdk synthの実行（dev環境）
  ```bash
  cdk synth DatabaseStack-dev --context env=dev
  ```
- [ ] **9.2.3** 合成成功の確認
  - CloudFormationテンプレートが生成されること
  - Secrets Managerが含まれていること
  - DBサブネットグループが含まれていること
  - DBセキュリティグループが含まれていること
  - Aurora Clusterが含まれていること（Writer + Reader）
  - インスタンスクラスがdb.t4g.smallであること
  - Performance Insightsが無効であること
  - エクスポートが5つ含まれていること
  - エラーが出ていないこと

**完了条件**: dev環境でのCDK合成が正常に完了すること

#### 9.3 CDK合成テスト（prod環境）
- [ ] **9.3.1** cdk synthの実行（prod環境）
  ```bash
  cdk synth DatabaseStack-prod --context env=prod
  ```
- [ ] **9.3.2** 合成成功の確認
  - CloudFormationテンプレートが生成されること
  - インスタンスクラスがdb.r6g.largeであること
  - Performance Insightsが有効であること
  - 削除保護が有効であること
  - 削除ポリシーがSNAPSHOTであること
  - エラーが出ていないこと

**完了条件**: prod環境でのCDK合成が正常に完了すること

---

### 10. デプロイテスト（dev環境）
- [ ] **10.1** AWS_PROFILEとAWS_REGIONを設定
  ```bash
  export AWS_PROFILE=takahata
  export AWS_REGION=ap-northeast-1
  ```
- [ ] **10.2** DatabaseStack-devのデプロイ
  ```bash
  cdk deploy DatabaseStack-dev --context env=dev --require-approval never
  ```
- [ ] **10.3** デプロイ成功の確認
  - CloudFormation Stackが作成されていること
  - Secrets Managerシークレットが作成されていること
  - DBサブネットグループが作成されていること
  - DBセキュリティグループが作成されていること
  - Aurora Clusterが作成されていること
  - Writer InstanceとReader Instanceが起動していること
  - 5つの出力値（エクスポート）が表示されていること

**完了条件**: dev環境へのデプロイが正常に完了すること

---

### 11. 動作確認

#### 11.1 Secrets Managerの確認
- [ ] **11.1.1** AWSコンソールでSecrets Managerを開く
- [ ] **11.1.2** シークレット名を確認（`dev/aurora/credentials`）
- [ ] **11.1.3** シークレット値を確認
  - usernameが`dbadmin`であること
  - passwordが自動生成されていること（32文字）

#### 11.2 Aurora Clusterの確認
- [ ] **11.2.1** AWSコンソールでRDSを開く
- [ ] **11.2.2** Aurora Clusterが作成されていること
- [ ] **11.2.3** Writer Instanceを確認
  - インスタンスクラス: db.t4g.small
  - AZ: ap-northeast-1a
  - ステータス: Available
  - Performance Insights: 無効
- [ ] **11.2.4** Reader Instanceを確認
  - インスタンスクラス: db.t4g.small
  - AZ: ap-northeast-1c
  - ステータス: Available
  - Performance Insights: 無効

#### 11.3 セキュリティ設定の確認
- [ ] **11.3.1** DBセキュリティグループを確認
  - インバウンドルール: ポート5432、送信元VPC CIDR
- [ ] **11.3.2** 暗号化を確認
  - 保存時暗号化が有効であること
- [ ] **11.3.3** 削除保護を確認
  - 開発環境では無効であること

#### 11.4 バックアップの確認
- [ ] **11.4.1** 自動バックアップを確認
  - バックアップ保持期間: 7日間
  - バックアップウィンドウ: 03:00-04:00 UTC

#### 11.5 CloudWatch Logsの確認
- [ ] **11.5.1** CloudWatch Logsを開く
- [ ] **11.5.2** PostgreSQLログが出力されていること
- [ ] **11.5.3** ログ保持期間: 7日間

#### 11.6 エクスポート値の確認
- [ ] **11.6.1** CloudFormation Stackの出力タブを開く
- [ ] **11.6.2** 5つのエクスポート値が表示されていること
  - DbClusterArn
  - DbClusterEndpoint
  - DbClusterReadEndpoint
  - DbSecretArn
  - DbSecurityGroupId

**完了条件**: すべてのリソースが正常に動作していること

---

## 全体の完了条件

以下のすべてが満たされていること：
- [ ] DatabaseStackが実装されている
- [ ] Secrets Managerでデータベース認証情報が管理されている
- [ ] Aurora PostgreSQL Clusterが作成されている（Writer + Reader）
- [ ] マルチAZ構成でデプロイされている（AZ-1とAZ-2）
- [ ] DBサブネットグループが正しく構成されている
- [ ] DBセキュリティグループが作成されている
- [ ] KMSによる保存時暗号化が有効化されている
- [ ] 環境別の設定が正しく適用されている
  - インスタンスクラス（dev: db.t4g.small、prod: db.r6g.large）
  - バックアップ保持（dev: 7日、prod: 30日）
  - 削除保護（dev: 無効、prod: 有効）
  - Performance Insights（dev: 無効、prod: 有効）
- [ ] CloudWatch Logsへのログエクスポートが有効化されている
- [ ] 5つのエクスポート値が設定されている
- [ ] TypeScriptのコンパイルが正常に完了している
- [ ] dev環境とprod環境でのCDK合成が正常に完了している
- [ ] dev環境へのデプロイが正常に完了している
- [ ] すべてのリソースが正常に動作している

## トラブルシューティング

### TypeScriptコンパイルエラーが出る場合
1. インポートパスを確認
2. 型定義の確認（rds.DatabaseCluster、ec2.SecurityGroup など）
3. インスタンスタイプの指定方法を確認
4. エラーメッセージを詳細に確認し、コードを修正

### cdk synthが失敗する場合
1. AWS認証情報が正しく設定されているか確認
2. NetworkStackがデプロイ済みか確認（VPCとサブネットのインポートに必要）
3. bin/app.tsのsyntaxエラーがないか確認
4. DatabaseStackの実装にエラーがないか確認
5. 環境設定（config）が正しいか確認

### Aurora Clusterが起動しない場合
1. DBサブネットグループの設定を確認
2. プライベートサブネットが2つのAZに配置されているか確認
3. セキュリティグループの設定を確認
4. インスタンスタイプの指定が正しいか確認
5. CloudFormation Stackのイベントログを確認

### VPCインポートが失敗する場合
1. NetworkStackがデプロイされているか確認
2. エクスポート名が正しいか確認（`${envName}-VpcId`など）
3. CloudFormation Stackの出力タブでエクスポート値を確認

### Secrets Managerの作成が失敗する場合
1. シークレット名の重複がないか確認
2. JSON構造が正しいか確認
3. パスワード生成の設定を確認

### Performance Insightsの設定エラー
1. 本番環境でのみ有効化されているか確認
2. 保持期間が7日間（無料枠）に設定されているか確認
3. インスタンスタイプがPerformance Insightsをサポートしているか確認

## 次のステップ

すべてのタスクが完了したら、フェーズ5（ECSStack）に進みます。

フェーズ5では以下を実装します：
- ECS Cluster
- ECR Repository
- ECS Task Definition（データベース接続設定を含む）
- ECS Service
- Application Load Balancer
- ALB Target Group
- ECSセキュリティグループ
- **DBセキュリティグループのインバウンドルール更新**
  - 現在: VPC CIDR全体からアクセス許可
  - 更新後: ECSセキュリティグループからのみアクセス許可
- Route 53レコード（カスタムドメイン）
- ACM証明書

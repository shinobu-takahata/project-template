# フェーズ3: セキュリティ基盤 - タスクリスト

## 概要
SecurityStackの実装タスクを管理します。

## タスク一覧

### 1. SecurityStackファイルの作成
- [ ] **1.1** `lib/stacks/security-stack.ts`の作成
- [ ] **1.2** 必要なインポートの追加
  - aws-cdk-lib（Stack, StackProps, RemovalPolicy, CfnOutput, Fn）
  - aws-cdk-lib/aws-guardduty
  - aws-cdk-lib/aws-config
  - aws-cdk-lib/aws-wafv2
  - aws-cdk-lib/aws-s3
  - aws-cdk-lib/aws-iam
  - constructs
  - ../config/env-config
- [ ] **1.3** SecurityStackPropsインターフェースの定義
- [ ] **1.4** SecurityStackクラスの定義

**完了条件**: SecurityStackの基本構造が作成されていること

---

### 2. GuardDuty Detectorの実装
- [ ] **2.1** GuardDuty Detectorリソースの作成
  - enable: true
  - dataSources設定
    - s3Logs: { enable: true }
    - kubernetes: { auditLogs: { enable: false } }
    - malwareProtection: 無効
- [ ] **2.2** タグ付け
  - Environment: config.envName
  - Project: project-template
  - ManagedBy: CDK

**完了条件**: GuardDuty Detectorが正しく設定されていること

---

### 3. AWS Config S3バケットの実装
- [ ] **3.1** S3バケットリソースの作成
  - バケット名: `config-${config.envName}-${this.account}`
  - 暗号化: S3_MANAGED
  - バージョニング: true
  - パブリックアクセスブロック: BLOCK_ALL
  - 削除ポリシー: 環境設定に従う
  - autoDeleteObjects: 環境設定に従う
- [ ] **3.2** バケットポリシーの追加
  - AWS Configサービスからのバケット書き込みを許可
  - AWS ConfigサービスからのバケットACL取得を許可
- [ ] **3.3** タグ付け

**完了条件**: Config S3バケットが正しく作成されていること

---

### 4. AWS Config IAMロールの実装
- [ ] **4.1** IAMロールリソースの作成
  - AssumedBy: config.amazonaws.com
  - マネージドポリシー: service-role/ConfigRole
- [ ] **4.2** S3バケットへの書き込み権限付与

**完了条件**: Config IAMロールが正しく作成されていること

---

### 5. Config Recorderの実装
- [ ] **5.1** Config Recorderリソースの作成
  - name: `config-recorder-${config.envName}`
  - roleArn: configRole.roleArn
  - recordingGroup:
    - allSupported: true
    - includeGlobalResourceTypes: true

**完了条件**: Config Recorderが正しく設定されていること

---

### 6. Delivery Channelの実装
- [ ] **6.1** Delivery Channelリソースの作成
  - name: `config-delivery-${config.envName}`
  - s3BucketName: configBucket.bucketName
  - configSnapshotDeliveryProperties:
    - deliveryFrequency: TwentyFour_Hours
- [ ] **6.2** 依存関係の設定
  - deliveryChannel.addDependency(recorder)

**完了条件**: Delivery Channelが正しく設定されていること

---

### 7. WAF Web ACLの実装
- [ ] **7.1** Web ACLリソースの作成
  - scope: REGIONAL
  - defaultAction: { allow: {} }
  - visibilityConfig設定
- [ ] **7.2** ルール1の追加（AWSManagedRulesCommonRuleSet）
  - priority: 1
  - managedRuleGroupStatement設定
  - overrideAction: { none: {} }
  - visibilityConfig設定
- [ ] **7.3** ルール2の追加（AWSManagedRulesKnownBadInputsRuleSet）
  - priority: 2
  - managedRuleGroupStatement設定
  - overrideAction: { none: {} }
  - visibilityConfig設定
- [ ] **7.4** ルール3の追加（AWSManagedRulesSQLiRuleSet）
  - priority: 3
  - managedRuleGroupStatement設定
  - overrideAction: { none: {} }
  - visibilityConfig設定
- [ ] **7.5** Web ACL ARNのエクスポート
  - exportName: `${config.envName}-WebAclArn`

**完了条件**: WAF Web ACLが3つのルールとともに正しく設定されていること

---

### 8. エントリーポイントの更新
- [ ] **8.1** `bin/app.ts`を開く
- [ ] **8.2** SecurityStackのインポート追加
  ```typescript
  import { SecurityStack } from '../lib/stacks/security-stack';
  ```
- [ ] **8.3** SecurityStackの作成追加（NetworkStackの後）
  ```typescript
  const securityStack = new SecurityStack(app, `SecurityStack-${envName}`, {
    env,
    config
  });
  ```

**完了条件**: bin/app.tsが更新され、SecurityStackが作成されること

---

### 9. ビルドと検証

#### 9.1 TypeScriptコンパイル
- [ ] **9.1.1** npm run buildの実行
  ```bash
  npm run build
  ```
- [ ] **9.1.2** コンパイル成功の確認
  - `lib/stacks/security-stack.js`が生成されていること
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
  cdk synth SecurityStack-dev --context env=dev
  ```
- [ ] **9.2.3** 合成成功の確認
  - CloudFormationテンプレートが生成されること
  - GuardDuty Detectorが含まれていること
  - Config Recorder、Delivery Channel、S3バケットが含まれていること
  - WAF Web ACLが含まれていること
  - エラーが出ていないこと

**完了条件**: dev環境でのCDK合成が正常に完了すること

#### 9.3 CDK合成テスト（prod環境）
- [ ] **9.3.1** cdk synthの実行（prod環境）
  ```bash
  cdk synth SecurityStack-prod --context env=prod
  ```
- [ ] **9.3.2** 合成成功の確認
  - CloudFormationテンプレートが生成されること
  - 削除ポリシーがRETAINに設定されていること
  - エラーが出ていないこと

**完了条件**: prod環境でのCDK合成が正常に完了すること

---

### 10. デプロイテスト（dev環境）
- [ ] **10.1** AWS_PROFILEとAWS_REGIONを設定
  ```bash
  export AWS_PROFILE=takahata
  export AWS_REGION=ap-northeast-1
  ```
- [ ] **10.2** SecurityStack-devのデプロイ
  ```bash
  cdk deploy SecurityStack-dev --context env=dev --require-approval never
  ```
- [ ] **10.3** デプロイ成功の確認
  - CloudFormation Stackが作成されていること
  - GuardDuty Detectorが有効化されていること
  - Config Recorderが起動していること
  - Config S3バケットが作成されていること
  - WAF Web ACLが作成されていること
  - Web ACL ARNが出力されていること

**完了条件**: dev環境へのデプロイが正常に完了すること

---

### 11. 動作確認
- [ ] **11.1** GuardDutyコンソールで確認
  - Detectorが有効化されていること
  - データソースが設定されていること
- [ ] **11.2** AWS Configコンソールで確認
  - Recorderが記録中であること
  - Delivery Channelが設定されていること
  - S3バケットにデータが配信されていること
- [ ] **11.3** WAFコンソールで確認
  - Web ACLが作成されていること
  - 3つのルールが設定されていること
  - CloudWatch Metricsが有効であること

**完了条件**: すべてのリソースが正常に動作していること

---

## 全体の完了条件

以下のすべてが満たされていること：
- [ ] SecurityStackが実装されている
- [ ] GuardDuty Detectorが有効化されている
- [ ] AWS Configが設定されている（Recorder、Delivery Channel、S3バケット、IAMロール）
- [ ] WAF Web ACLが作成されている（3つのマネージドルールセット）
- [ ] TypeScriptのコンパイルが正常に完了している
- [ ] dev環境とprod環境でのCDK合成が正常に完了している
- [ ] dev環境へのデプロイが正常に完了している
- [ ] すべてのリソースが正常に動作している

## トラブルシューティング

### TypeScriptコンパイルエラーが出る場合
1. インポートパスを確認
2. 型定義の確認
3. エラーメッセージを詳細に確認し、コードを修正

### cdk synthが失敗する場合
1. AWS認証情報が正しく設定されているか確認
2. bin/app.tsのsyntaxエラーがないか確認
3. SecurityStackの実装にエラーがないか確認

### Config Recorderが起動しない場合
1. IAMロールの権限を確認
2. S3バケットポリシーを確認
3. Delivery Channelの依存関係を確認
4. CloudFormation Stackのイベントログを確認

### WAF Web ACLの作成が失敗する場合
1. リージョンが正しいか確認（ap-northeast-1）
2. ルール設定の構文を確認
3. CloudFormation Stackのエラーメッセージを確認

## 次のステップ
すべてのタスクが完了したら、フェーズ4（DatabaseStack）に進みます。

フェーズ4では以下を実装します：
- Aurora PostgreSQL Cluster（プロビジョニング型）
- DBサブネットグループ
- セキュリティグループ
- Secrets Manager統合
- Performance Insights（本番環境）

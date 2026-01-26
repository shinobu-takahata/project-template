# フェーズ7: CI/CD統合 - タスクリスト

## タスク一覧

### 1. 環境設定の拡張
- [ ] 1.1 `lib/config/env-config.ts` に GitHub設定の型定義を追加
- [ ] 1.2 `lib/config/dev.ts` に GitHub設定を追加
- [ ] 1.3 `lib/config/prod.ts` に GitHub設定を追加

### 2. ComputeStack への実装
- [ ] 2.1 OIDC Providerの作成
- [ ] 2.2 GitHub Actions用IAMロールの作成
- [ ] 2.3 ECR関連のIAMポリシー追加
- [ ] 2.4 ECS関連のIAMポリシー追加
- [ ] 2.5 PassRoleのIAMポリシー追加
- [ ] 2.6 CfnOutputの追加（ロールARN、プロバイダーARN）

### 3. 検証
- [ ] 3.1 CDK synthの実行と確認
- [ ] 3.2 CDK diffの実行と確認

## 完了条件
- [ ] すべてのタスクが完了
- [ ] CDK synthがエラーなく完了
- [ ] 生成されるCloudFormationテンプレートにOIDC Provider、IAMロールが含まれる

## 進捗状況

| タスク | ステータス | 備考 |
|-------|----------|------|
| 1.1 env-config.ts 型定義追加 | 未着手 | |
| 1.2 dev.ts GitHub設定追加 | 未着手 | |
| 1.3 prod.ts GitHub設定追加 | 未着手 | |
| 2.1 OIDC Provider作成 | 未着手 | |
| 2.2 IAMロール作成 | 未着手 | |
| 2.3 ECR IAMポリシー追加 | 未着手 | |
| 2.4 ECS IAMポリシー追加 | 未着手 | |
| 2.5 PassRole IAMポリシー追加 | 未着手 | |
| 2.6 CfnOutput追加 | 未着手 | |
| 3.1 CDK synth実行 | 未着手 | |
| 3.2 CDK diff実行 | 未着手 | |

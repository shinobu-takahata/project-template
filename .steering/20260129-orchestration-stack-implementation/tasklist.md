# タスクリスト: OrchestrationStack実装

## 概要
EventBridgeとStep Functionsによるワークフロー制御基盤（OrchestrationStack）の実装タスクリスト。
既存のECSタスク定義をcontainerOverridesで再利用し、Pythonバッチスクリプトを定期実行する。

## タスク一覧

### フェーズ1: 環境設定の拡張

- [ ] **1.1 env-config.tsにorchestration設定インターフェース追加**
  - ファイル: `cdk/lib/config/env-config.ts`
  - EnvConfigインターフェースにorchestrationフィールド追加
  - 設定項目:
    - enabled: boolean（スケジュール実行の有効/無効）
    - scheduleExpression: string（cron式）
    - batchScriptPath: string（バッチスクリプトのパス）

- [ ] **1.2 dev.tsにorchestration設定追加**
  - ファイル: `cdk/lib/config/dev.ts`
  - enabled: false（開発環境では無効化）
  - scheduleExpression: 'cron(0 17 * * ? *)'（JST午前2時）
  - batchScriptPath: '/app/batch/sample_batch.py'

- [ ] **1.3 prod.tsにorchestration設定追加**
  - ファイル: `cdk/lib/config/prod.ts`
  - enabled: true（本番環境では有効化）
  - scheduleExpression: 'cron(0 17 * * ? *)'（JST午前2時）
  - batchScriptPath: '/app/batch/sample_batch.py'

### フェーズ2: ComputeStackの更新

- [ ] **2.1 TaskDefinitionArnのCfnOutput追加**
  - ファイル: `cdk/lib/stacks/compute-stack.ts`
  - exportName: `${config.envName}-TaskDefinitionArn`

- [ ] **2.2 TaskRoleArnのCfnOutput追加**
  - ファイル: `cdk/lib/stacks/compute-stack.ts`
  - exportName: `${config.envName}-TaskRoleArn`

- [ ] **2.3 TaskExecutionRoleArnのCfnOutput追加**
  - ファイル: `cdk/lib/stacks/compute-stack.ts`
  - exportName: `${config.envName}-TaskExecutionRoleArn`

- [ ] **2.4 PrivateSubnetIdsのCfnOutput追加**
  - ファイル: `cdk/lib/stacks/compute-stack.ts`
  - exportName: `${config.envName}-PrivateSubnetIds`
  - カンマ区切りの文字列として出力

- [ ] **2.5 EcsSecurityGroupIdのCfnOutput追加（未存在の場合）**
  - ファイル: `cdk/lib/stacks/compute-stack.ts`
  - exportName: `${config.envName}-EcsSecurityGroupId`

### フェーズ3: OrchestrationStackの実装

- [ ] **3.1 OrchestrationStackファイル作成**
  - ファイル: `cdk/lib/stacks/orchestration-stack.ts`
  - スタッククラス定義（OrchestrationStackProps継承）
  - コンストラクタでconfigを受け取る

- [ ] **3.2 CloudWatch Logsロググループ作成**
  - ロググループ名: `/aws/stepfunctions/${config.envName}-sample-batch-workflow`
  - 保持期間: config.logRetentionDays
  - 削除ポリシー: config.removalPolicy.logGroups

- [ ] **3.3 Step Functions実行用IAMロール作成**
  - ロール名: `stepfunctions-role-${config.envName}`
  - 権限:
    - ecs:RunTask, ecs:StopTask, ecs:DescribeTasks
    - iam:PassRole（TaskRole、TaskExecutionRole）
    - sns:Publish
    - logs:CreateLogStream, logs:PutLogEvents

- [ ] **3.4 Step Functionsステートマシン作成**
  - ステートマシン名: `${config.envName}-sample-batch-workflow`
  - EcsRunTaskタスク（containerOverridesでバッチスクリプト実行）
  - リトライ設定（最大3回、指数バックオフ）
  - エラー時SNS通知（MonitoringStackのCriticalAlertsTopic）
  - ログ設定（LogLevel.ALL）

- [ ] **3.5 EventBridge実行用IAMロール作成**
  - ロール名: `eventbridge-role-${config.envName}`
  - 権限: states:StartExecution

- [ ] **3.6 EventBridgeルール作成**
  - ルール名: `${config.envName}-sample-batch-schedule`
  - スケジュール式: config.orchestration.scheduleExpression
  - enabled: config.orchestration.enabled
  - ターゲット: Step Functionsステートマシン

- [ ] **3.7 CfnOutput追加**
  - StateMachineArn
  - EventBridgeRuleName

### フェーズ4: app.tsの更新

- [ ] **4.1 OrchestrationStackのインポート追加**
  - ファイル: `cdk/bin/app.ts`
  - import { OrchestrationStack } from '../lib/stacks/orchestration-stack';

- [ ] **4.2 OrchestrationStackのインスタンス作成**
  - `OrchestrationStack-${envName}`として作成
  - env, configを渡す

- [ ] **4.3 依存関係の設定**
  - orchestrationStack.addDependency(computeStack)
  - orchestrationStack.addDependency(monitoringStack)

### フェーズ5: Pythonバッチスクリプト作成

- [ ] **5.1 バッチディレクトリ作成**
  - ディレクトリ: `backend/batch/`
  - `__init__.py`を作成（空ファイル）

- [ ] **5.2 sample_batch.py作成**
  - ファイル: `backend/batch/sample_batch.py`
  - 処理内容:
    - ログ設定（標準出力）
    - データベース接続（既存のapp.databaseを使用）
    - データ参照（SELECT）のサンプル
    - データ登録（INSERT/UPDATE）のサンプル
    - エラーハンドリングと終了コード

### フェーズ6: 検証とデプロイ

- [ ] **6.1 cdk synthによる構文チェック**
  - コマンド: `docker compose --profile cdk run --rm cdk cdk synth --context env=dev`
  - エラーがないことを確認

- [ ] **6.2 cdk diffによる差分確認**
  - コマンド: `docker compose --profile cdk run --rm -e AWS_PROFILE=takahata cdk cdk diff --all --context env=dev`
  - 作成されるリソースを確認

- [ ] **6.3 開発環境へのデプロイ**
  - コマンド: `docker compose --profile cdk run --rm -e AWS_PROFILE=takahata cdk cdk deploy --all --context env=dev --require-approval never`
  - OrchestrationStackが作成されることを確認
  - EventBridgeルールが無効化されていることを確認

- [ ] **6.4 動作確認（手動実行）**
  - AWSコンソールでStep Functionsステートマシンを手動実行
  - CloudWatch Logsで実行ログを確認
  - ECSタスクが起動し、バッチスクリプトが実行されることを確認

## 完了条件
- [ ] すべてのタスクが完了している
- [ ] cdk synthでエラーが発生しない
- [ ] OrchestrationStackが正しく作成される
- [ ] Step Functionsステートマシンが手動実行で正常動作する
- [ ] EventBridgeルールが作成される（開発環境では無効化状態）
- [ ] バッチスクリプトのログがCloudWatch Logsに出力される

## 依存関係
```
フェーズ1（環境設定）─┐
                    ├─→ フェーズ3（OrchestrationStack）─→ フェーズ4（app.ts）─┐
フェーズ2（ComputeStack更新）─┘                                              ├─→ フェーズ6（検証）
                                                                            │
フェーズ5（Pythonバッチ）────────────────────────────────────────────────────┘
```

## 注意事項
- CDKコマンドはすべてdocker compose経由で実行すること
  - 基本形式: `docker compose --profile cdk run --rm cdk <command>`
  - AWS認証が必要な場合: `-e AWS_PROFILE=takahata`を追加
- ファイルパスは `cdk/lib/` 配下であることを確認
- IAMロールの権限は最小権限の原則に従う
- CloudWatch Logsのログ保持期間は環境設定に従う

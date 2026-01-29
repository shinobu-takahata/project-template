# 設計書: OrchestrationStack実装

## 概要
AWS CDKを使用して、EventBridgeとStep Functionsによるワークフロー制御基盤を構築します。これはフェーズ8（8.2, 8.3）のオプション機能として、将来的な拡張を見据えた実装を提供します。

基本的なユースケースとして、ECSタスクのスケジュール実行を想定したサンプル実装を提供します。既存のAPI用タスク定義を再利用し、containerOverridesでPythonバッチスクリプトを実行する方式を採用します。

## 実装アプローチ

### 基本方針
1. **シンプルさ優先**: 新しいタスク定義は作成せず、既存のAPI用タスク定義を再利用
2. **柔軟性の確保**: 将来的に複雑なワークフローを追加しやすい構造
3. **コスト最適化**: 開発環境ではスケジュール実行を無効化
4. **既存リソースの活用**: MonitoringStackのSNSトピック、ComputeStackのECSリソースを参照

### アーキテクチャ概要
```
EventBridge Rule (cron式)
    ↓ (トリガー)
Step Functions State Machine
    ↓ (ECS RunTask)
ECS Fargate Task (既存タスク定義 + containerOverrides)
    ↓ (実行)
Python Batch Script (backend/batch/sample_batch.py)
    ↓ (DB操作)
Aurora PostgreSQL
    ↓ (エラー時)
SNS Topic (MonitoringStack) → メール通知
```

## 変更対象コンポーネント

### 1. CDK新規スタック

#### 1.1 OrchestrationStack
**ファイル**: `cdk/lib/stacks/orchestration-stack.ts`

**責務**:
- Step Functionsステートマシンの作成
- EventBridgeルールの作成
- IAMロールの作成
- スタック間連携（ComputeStack、MonitoringStack）

**主要リソース**:
- `sfn.StateMachine`: ワークフロー定義
- `events.Rule`: スケジュール実行トリガー
- `iam.Role`: Step Functions実行ロール、EventBridge実行ロール
- `logs.LogGroup`: Step Functions実行ログ

### 2. CDK環境設定

#### 2.1 環境設定インターフェース拡張
**ファイル**: `cdk/lib/config/env-config.ts`

**追加内容**:
```typescript
export interface EnvConfig {
  // 既存フィールド...

  // オーケストレーション設定（追加）
  orchestration?: {
    // スケジュール実行の有効/無効
    enabled: boolean;

    // cron式（UTC）
    // デフォルト: cron(0 17 * * ? *) = JST午前2時
    scheduleExpression: string;

    // バッチスクリプトのパス（コンテナ内）
    batchScriptPath: string;
  };
}
```

#### 2.2 開発環境設定
**ファイル**: `cdk/lib/config/dev.ts`

**追加内容**:
```typescript
export const devConfig: EnvConfig = {
  // 既存設定...

  orchestration: {
    enabled: false,  // 開発環境では無効化
    scheduleExpression: 'cron(0 17 * * ? *)',
    batchScriptPath: '/app/batch/sample_batch.py',
  },
};
```

#### 2.3 本番環境設定
**ファイル**: `cdk/lib/config/prod.ts`

**追加内容**:
```typescript
export const prodConfig: EnvConfig = {
  // 既存設定...

  orchestration: {
    enabled: true,  // 本番環境では有効化
    scheduleExpression: 'cron(0 17 * * ? *)',
    batchScriptPath: '/app/batch/sample_batch.py',
  },
};
```

### 3. CDKアプリケーション

#### 3.1 app.ts更新
**ファイル**: `cdk/bin/app.ts`

**追加内容**:
```typescript
import { OrchestrationStack } from '../lib/stacks/orchestration-stack';

// 既存スタック作成...

// OrchestrationStackの作成（Phase 8）
const orchestrationStack = new OrchestrationStack(
  app,
  `OrchestrationStack-${envName}`,
  {
    env,
    config,
  }
);

// 依存関係の設定
orchestrationStack.addDependency(computeStack);
orchestrationStack.addDependency(monitoringStack);
```

### 4. Pythonバッチスクリプト

#### 4.1 サンプルバッチスクリプト
**ファイル**: `backend/batch/sample_batch.py`

**責務**:
- データベースへの接続
- データの参照（SELECT）
- データの登録（INSERT/UPDATE）
- 適切なログ出力

**実装方針**:
- 既存のデータベース接続ロジックを再利用（`app/database.py`）
- 環境変数から接続情報を取得（既存タスク定義から継承）
- 標準出力にログを出力（CloudWatch Logsに自動転送）
- エラー時は適切な終了コードを返す

**サンプル処理内容**:
```python
# 1. データベース接続
# 2. サンプルデータの集計（SELECT）
# 3. 集計結果の保存（INSERT/UPDATE）
# 4. 処理結果をログ出力
```

## データ構造の変更

### 環境設定の追加
新しいフィールド `orchestration` を `EnvConfig` インターフェースに追加します。

```typescript
orchestration?: {
  enabled: boolean;
  scheduleExpression: string;
  batchScriptPath: string;
}
```

### Step Functionsステートマシン定義
CDK L2 Constructを使用して、以下のステート定義を作成します。

```typescript
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as tasks from 'aws-cdk-lib/aws-stepfunctions-tasks';

// ECS RunTask（containerOverridesでバッチスクリプトを実行）
const runTask = new tasks.EcsRunTask(this, 'RunBatchTask', {
  cluster: ecsCluster,
  taskDefinition: taskDefinition,
  launchTarget: new tasks.EcsFargateLaunchTarget(),
  containerOverrides: [
    {
      containerName: 'backend',
      command: ['python', batchScriptPath],
    },
  ],
  integrationPattern: sfn.IntegrationPattern.RUN_JOB,  // タスク完了まで待機
});

// エラー時のSNS通知
const notifyError = new tasks.SnsPublish(this, 'NotifyError', {
  topic: snsTopic,
  message: sfn.TaskInput.fromJsonPathAt('$'),
});

// ステートマシン定義
const definition = runTask
  .addCatch(notifyError, {
    errors: ['States.ALL'],
    resultPath: '$.error',
  })
  .next(new sfn.Succeed(this, 'Success'));
```

## 影響範囲

### 既存リソースへの影響

#### 1. ComputeStack（参照のみ、変更なし）
**参照リソース**:
- `EcsCluster`: ECSクラスター
- `TaskDefinition`: 既存タスク定義（ARNを参照）
- `TaskRole`: タスクロール（ECS実行権限を追加）
- `TaskExecutionRole`: タスク実行ロール

**CfnOutputからインポート**:
```typescript
const ecsClusterName = Fn.importValue(`${config.envName}-EcsClusterName`);
const ecsServiceName = Fn.importValue(`${config.envName}-EcsServiceName`);
```

**既存タスク定義の参照**:
ComputeStackでタスク定義ARNをCfnOutputとしてエクスポートする必要があります（後述の「必要な追加CfnOutput」参照）。

#### 2. MonitoringStack（参照のみ、変更なし）
**参照リソース**:
- `CriticalAlertsTopic`: エラー通知用SNSトピック

**CfnOutputからインポート**:
```typescript
const snsTopicArn = Fn.importValue(`${config.envName}-CriticalAlertsTopicArn`);
```

#### 3. NetworkStack（参照のみ、変更なし）
**参照リソース**:
- `VPC`: VPCサブネット情報（ECSタスク起動時に使用）

**CfnOutputからインポート**:
```typescript
const vpc = ec2.Vpc.fromVpcAttributes(this, 'VPC', {
  vpcId: Fn.importValue(`${config.envName}-VpcId`),
  // ...
});
```

### 必要な追加CfnOutput

#### ComputeStack (`cdk/lib/stacks/compute-stack.ts`)
現在のComputeStackにタスク定義ARNのエクスポートが存在しないため、以下を追加する必要があります。

```typescript
// 既存コードの最後に追加
new CfnOutput(this, 'TaskDefinitionArn', {
  value: taskDefinition.taskDefinitionArn,
  description: 'ECS Task Definition ARN',
  exportName: `${config.envName}-TaskDefinitionArn`,
});

new CfnOutput(this, 'TaskRoleArn', {
  value: taskRole.roleArn,
  description: 'ECS Task Role ARN',
  exportName: `${config.envName}-TaskRoleArn`,
});

new CfnOutput(this, 'TaskExecutionRoleArn', {
  value: executionRole.roleArn,
  description: 'ECS Task Execution Role ARN',
  exportName: `${config.envName}-TaskExecutionRoleArn`,
});

// プライベートサブネットID（ECSタスク起動時に必要）
new CfnOutput(this, 'PrivateSubnetIds', {
  value: Fn.join(',', vpc.isolatedSubnets.map(subnet => subnet.subnetId)),
  description: 'Private Subnet IDs (comma-separated)',
  exportName: `${config.envName}-PrivateSubnetIds`,
});

// ECSセキュリティグループID（既にエクスポート済み）
// exportName: `${config.envName}-EcsSecurityGroupId`
```

### 新規リソースの追加

#### 1. Step Functions実行ロール
**権限**:
- ECS RunTask（`ecs:RunTask`, `ecs:DescribeTasks`, `ecs:StopTask`）
- SNS Publish（`sns:Publish`）
- CloudWatch Logs書き込み（`logs:CreateLogStream`, `logs:PutLogEvents`）
- IAM PassRole（タスク実行ロール、タスクロール用）

#### 2. EventBridge実行ロール
**権限**:
- Step Functions実行（`states:StartExecution`）

#### 3. CloudWatch Logsロググループ
**設定**:
- ロググループ名: `/aws/stepfunctions/${config.envName}-sample-batch-workflow`
- 保持期間: `config.logRetentionDays`
- 削除ポリシー: `config.removalPolicy.logGroups`

## 技術的な設計詳細

### 1. Step Functionsステートマシン

#### ステート定義
```typescript
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as tasks from 'aws-cdk-lib/aws-stepfunctions-tasks';

// ECS RunTask
const runBatchTask = new tasks.EcsRunTask(this, 'RunBatchTask', {
  cluster: cluster,
  taskDefinition: taskDefinition,
  launchTarget: new tasks.EcsFargateLaunchTarget({
    platformVersion: ecs.FargatePlatformVersion.LATEST,
  }),
  containerOverrides: [
    {
      containerName: 'backend',
      command: ['python', config.orchestration.batchScriptPath],
    },
  ],
  subnets: {
    subnets: isolatedSubnets,
  },
  securityGroups: [ecsSecurityGroup],
  integrationPattern: sfn.IntegrationPattern.RUN_JOB,
  resultPath: '$.taskResult',
});

// リトライ設定
runBatchTask.addRetry({
  errors: ['States.TaskFailed'],
  interval: Duration.seconds(30),
  maxAttempts: 3,
  backoffRate: 2.0,
});

// エラー時のSNS通知
const notifyFailure = new tasks.SnsPublish(this, 'NotifyFailure', {
  topic: snsTopic,
  message: sfn.TaskInput.fromObject({
    error: sfn.JsonPath.stringAt('$.error.Error'),
    cause: sfn.JsonPath.stringAt('$.error.Cause'),
    executionName: sfn.JsonPath.stringAt('$$.Execution.Name'),
    timestamp: sfn.JsonPath.stringAt('$$.State.EnteredTime'),
  }),
  subject: `[${config.envName}] Batch Execution Failed`,
});

// 成功時の処理
const succeed = new sfn.Succeed(this, 'Success');

// ステートマシン定義
const definition = runBatchTask
  .addCatch(notifyFailure, {
    errors: ['States.ALL'],
    resultPath: '$.error',
  })
  .next(succeed);
```

#### ステートマシン作成
```typescript
const stateMachine = new sfn.StateMachine(this, 'SampleBatchWorkflow', {
  stateMachineName: `${config.envName}-sample-batch-workflow`,
  definition: definition,
  logs: {
    destination: logGroup,
    level: sfn.LogLevel.ALL,
    includeExecutionData: true,
  },
  tracingEnabled: true,
});
```

### 2. EventBridgeルール

#### ルール定義
```typescript
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';

const rule = new events.Rule(this, 'ScheduleRule', {
  ruleName: `${config.envName}-sample-batch-schedule`,
  description: 'Trigger sample batch workflow daily at 2:00 AM JST',
  schedule: events.Schedule.expression(config.orchestration.scheduleExpression),
  enabled: config.orchestration.enabled,  // 開発環境では無効化
});

rule.addTarget(
  new targets.SfnStateMachine(stateMachine, {
    input: events.RuleTargetInput.fromObject({
      triggerSource: 'EventBridge',
      timestamp: events.EventField.time,
    }),
  })
);
```

### 3. IAMロール設計

#### Step Functions実行ロール
```typescript
const stateMachineRole = new iam.Role(this, 'StateMachineRole', {
  roleName: `stepfunctions-role-${config.envName}`,
  assumedBy: new iam.ServicePrincipal('states.amazonaws.com'),
});

// ECS RunTask権限
stateMachineRole.addToPolicy(
  new iam.PolicyStatement({
    effect: iam.Effect.ALLOW,
    actions: [
      'ecs:RunTask',
      'ecs:StopTask',
      'ecs:DescribeTasks',
    ],
    resources: [taskDefinitionArn],
  })
);

// PassRole権限（タスク実行ロール、タスクロール）
stateMachineRole.addToPolicy(
  new iam.PolicyStatement({
    effect: iam.Effect.ALLOW,
    actions: ['iam:PassRole'],
    resources: [taskRoleArn, executionRoleArn],
    conditions: {
      StringEquals: {
        'iam:PassedToService': 'ecs-tasks.amazonaws.com',
      },
    },
  })
);

// SNS Publish権限
stateMachineRole.addToPolicy(
  new iam.PolicyStatement({
    effect: iam.Effect.ALLOW,
    actions: ['sns:Publish'],
    resources: [snsTopicArn],
  })
);

// CloudWatch Logs書き込み権限
logGroup.grantWrite(stateMachineRole);
```

#### EventBridge実行ロール
```typescript
const eventBridgeRole = new iam.Role(this, 'EventBridgeRole', {
  roleName: `eventbridge-role-${config.envName}`,
  assumedBy: new iam.ServicePrincipal('events.amazonaws.com'),
});

eventBridgeRole.addToPolicy(
  new iam.PolicyStatement({
    effect: iam.Effect.ALLOW,
    actions: ['states:StartExecution'],
    resources: [stateMachine.stateMachineArn],
  })
);
```

### 4. Pythonバッチスクリプト設計

#### ディレクトリ構造
```
backend/
├── batch/
│   ├── __init__.py
│   └── sample_batch.py
```

#### サンプル実装（`backend/batch/sample_batch.py`）
```python
#!/usr/bin/env python3
"""
サンプルバッチスクリプト

データベースにアクセスし、サンプルデータの集計・保存を行います。
"""
import sys
import logging
from datetime import datetime

# 既存のアプリケーションコードを再利用
from app.database import get_db_session
from app.models import SampleModel  # 適切なモデルに置き換え

# ログ設定（標準出力に出力）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def main():
    """メイン処理"""
    try:
        logger.info("Batch execution started")

        # データベースセッション取得
        db = next(get_db_session())

        # サンプル処理: データ集計
        logger.info("Aggregating data...")
        # count = db.query(SampleModel).count()
        # logger.info(f"Total records: {count}")

        # サンプル処理: データ登録
        logger.info("Inserting aggregation result...")
        # sample = SampleModel(
        #     name="batch_result",
        #     value=count,
        #     created_at=datetime.utcnow()
        # )
        # db.add(sample)
        # db.commit()

        logger.info("Batch execution completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Batch execution failed: {str(e)}", exc_info=True)
        return 1
    finally:
        if db:
            db.close()


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
```

### 5. コンテナコマンドオーバーライド

Step FunctionsからECSタスク起動時に、以下のようにコマンドを上書きします。

```typescript
containerOverrides: [
  {
    containerName: 'backend',
    command: ['python', '/app/batch/sample_batch.py'],
  },
],
```

これにより、既存のFastAPIコンテナイメージを使用しつつ、バッチスクリプトを実行できます。

## セキュリティ設計

### 1. IAMロール最小権限
- Step Functions実行ロール: ECS RunTask、SNS Publish、CloudWatch Logs書き込み権限のみ
- EventBridge実行ロール: Step Functions StartExecution権限のみ
- PassRole権限は`ecs-tasks.amazonaws.com`に限定

### 2. ネットワークセキュリティ
- ECSタスクはプライベートサブネットで実行
- 既存のECSセキュリティグループを使用（データベースアクセス許可済み）

### 3. データベースアクセス
- 既存のSecrets Manager認証情報を使用
- タスクロールは既存のデータベースアクセス権限を継承

## モニタリング設計

### 1. CloudWatch Logs
- Step Functions実行ログ: すべてのステート遷移を記録
- ECSタスクログ: Fluent Bit経由でCloudWatch Logs（エラーレベル）とS3（全ログ）に保存

### 2. CloudWatch Metrics
- Step Functions実行メトリクス（ExecutionsStarted、ExecutionsFailed、ExecutionTime）
- ECSタスクメトリクス（既存のモニタリング）

### 3. アラート
- ステートマシン実行失敗時: SNSトピックに通知
- ECSタスク失敗時: Step Functionsのリトライ機能で自動再試行（最大3回）

## コスト最適化

### 1. 開発環境での無効化
- `config.orchestration.enabled = false`で開発環境ではスケジュール実行を無効化
- 手動テスト時のみStep Functionsを実行

### 2. リソース使用の最適化
- 既存タスク定義を再利用（新規タスク定義作成不要）
- Step Functions標準ワークフロー（Express使用せず、コスト削減）

### 3. ログ保持期間
- 環境設定に応じた保持期間（dev: 7日、prod: 30日）

## 将来的な拡張性

### 1. 複雑なワークフローへの対応
現在のシンプルな「ECSタスク起動 → 完了待機」から、以下のような拡張が可能です。

```typescript
// 並列実行
const parallel = new sfn.Parallel(this, 'ParallelTasks');
parallel.branch(task1);
parallel.branch(task2);

// 条件分岐
const choice = new sfn.Choice(this, 'CheckResult');
choice.when(sfn.Condition.stringEquals('$.status', 'success'), successTask);
choice.otherwise(failureTask);

// マップ処理
const map = new sfn.Map(this, 'ProcessItems', {
  maxConcurrency: 5,
  itemsPath: '$.items',
});
map.iterator(processItemTask);
```

### 2. 複数バッチジョブの管理
新しいバッチジョブを追加する場合：

1. `backend/batch/new_batch.py`を作成
2. 新しいステートマシンを追加（OrchestrationStack内）
3. 新しいEventBridgeルールを追加

### 3. バッチ専用タスク定義の追加
将来的にバッチ処理が重くなった場合：

```typescript
// バッチ専用タスク定義を作成
const batchTaskDefinition = new ecs.FargateTaskDefinition(this, 'BatchTaskDef', {
  cpu: 2048,  // より大きなリソース
  memoryLimitMiB: 4096,
  // ...
});
```

## テスト戦略

### 1. 手動テスト
```bash
# Step Functionsステートマシンを手動実行
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:ap-northeast-1:ACCOUNT_ID:stateMachine:dev-sample-batch-workflow \
  --input '{"triggerSource":"manual","timestamp":"2026-01-29T12:00:00Z"}'
```

### 2. バッチスクリプトの単体テスト
```bash
# ローカル環境でPythonスクリプトを実行
cd backend
python batch/sample_batch.py
```

### 3. 統合テスト
- EventBridgeルールを手動で有効化
- 実行結果をCloudWatch Logsで確認
- SNS通知の受信確認

## リスクと対応策

### 1. 既存タスク定義への影響
**リスク**: containerOverridesの使用が既存のWebサービスに影響する可能性

**対応策**:
- containerOverridesはタスク起動時のパラメータであり、タスク定義自体は変更されない
- 既存のECSサービスには影響なし

### 2. データベース接続数
**リスク**: バッチ実行中にデータベース接続数が増加

**対応策**:
- MonitoringStackのアラームで接続数を監視（閾値: 80接続）
- 必要に応じてバッチ実行時間を調整

### 3. コスト増加
**リスク**: Step Functions実行コストが増加

**対応策**:
- 開発環境ではスケジュール実行を無効化
- 実行頻度を最小限に抑える（デフォルト: 1日1回）
- CloudWatch Costsでコスト監視

## まとめ

本設計は、以下の原則に基づいて実装されます。

1. **シンプルさ**: 既存リソースを最大限再利用
2. **拡張性**: 将来的な機能追加に対応できる柔軟な構造
3. **コスト最適化**: 開発環境でのコスト削減、リソース効率化
4. **セキュリティ**: 最小権限の原則、既存セキュリティ設定の継承
5. **モニタリング**: 既存のMonitoringStackとの統合、適切なエラーハンドリング

この設計により、フェーズ8のオプション機能として、将来的なワークフロー制御基盤を構築します。

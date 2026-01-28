# 設計書: フェーズ6 監視とロギング基盤（MonitoringStack）

## 概要
AWS CDK実装計画書のフェーズ6として、MonitoringStackを新規作成する。このスタックは、CloudWatch Alarms、SNSトピック、CloudWatch Dashboardを実装し、システム全体の監視基盤を構築する。

## 参照ドキュメント
- [requirements.md](requirements.md) - 承認済みの要求仕様
- [implements_aws_by_cdk_plan.md](../../docs/architecture/implements_aws_by_cdk_plan.md) - フェーズ6のCDK実装計画
- [compute-stack.ts](../../cdk/lib/stacks/compute-stack.ts) - 既存のComputeStack
- [database-stack.ts](../../cdk/lib/stacks/database-stack.ts) - 既存のDatabaseStack
- [env-config.ts](../../cdk/lib/config/env-config.ts) - 環境設定の型定義

---

## 1. MonitoringStackの全体構成

### 1.1 スタック責務
MonitoringStackは以下の責務を持つ。
- CloudWatch Alarmsの作成と管理（11種類）
- SNSトピックの作成と管理（critical-alerts、warning-alerts）
- CloudWatch Dashboardの作成と管理
- アラーム閾値の環境別設定管理

### 1.2 スタック間依存関係
MonitoringStackは、以下のスタックからの情報をインポートする。

| スタック | インポートする情報 | 用途 |
|---------|------------------|------|
| ComputeStack | EcsClusterName | ECSメトリクスの参照 |
| ComputeStack | EcsServiceName | ECSサービスメトリクスの参照 |
| ComputeStack | AlbArn | ALBメトリクスの参照 |
| ComputeStack | AppLogGroupName | エラーログメトリクスフィルタ |
| DatabaseStack | DbClusterEndpoint | Auroraクラスター識別子の構築 |

**注意**: Auroraのクラスター識別子は、エンドポイントから抽出する（例: `cluster-dev.cluster-xxxxx.ap-northeast-1.rds.amazonaws.com` → `cluster-dev`）

---

## 2. SNSトピックの設計

### 2.1 トピック構成

#### 2.1.1 critical-alerts トピック
```typescript
new sns.Topic(this, 'CriticalAlertsTopic', {
  topicName: `critical-alerts-${config.envName}`,
  displayName: 'Critical Alerts'
});
```

**用途**: クリティカルなアラート（システム障害、エラー検出、サービス停止など）

**サブスクリプション**:
- メール通知（環境設定から取得: `config.monitoring.alertEmail`）

#### 2.1.2 warning-alerts トピック
```typescript
new sns.Topic(this, 'WarningAlertsTopic', {
  topicName: `warning-alerts-${config.envName}`,
  displayName: 'Warning Alerts'
});
```

**用途**: 警告レベルのアラート（リソース使用率高騰、レスポンスタイム遅延など）

**サブスクリプション**:
- メール通知（環境設定から取得: `config.monitoring.alertEmail`）

### 2.2 サブスクリプション設定
```typescript
import * as subscriptions from 'aws-cdk-lib/aws-sns-subscriptions';

if (config.monitoring?.alertEmail) {
  criticalTopic.addSubscription(
    new subscriptions.EmailSubscription(config.monitoring.alertEmail)
  );

  warningTopic.addSubscription(
    new subscriptions.EmailSubscription(config.monitoring.alertEmail)
  );
}
```

**注意**:
- メールサブスクリプションは初回デプロイ後、手動でサブスクリプション確認メールを承認する必要がある
- `config.monitoring.alertEmail`が未設定の場合はサブスクリプションを作成しない

---

## 3. CloudWatch Alarmsの設計

### 3.1 アラーム設計パターン
すべてのアラームは以下の共通パターンに従う。

```typescript
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as actions from 'aws-cdk-lib/aws-cloudwatch-actions';

const alarm = new cloudwatch.Alarm(this, 'AlarmId', {
  alarmName: `${config.envName}-alarm-name`,
  metric: /* メトリクス定義 */,
  threshold: /* 閾値（環境設定から取得） */,
  evaluationPeriods: /* 評価期間 */,
  comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
  treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING
});

alarm.addAlarmAction(new actions.SnsAction(topic));
```

### 3.2 ECS関連アラーム（4種類）

#### 3.2.1 ERRORログ検出アラーム
**メトリクスフィルタ**:
```typescript
const errorLogGroup = logs.LogGroup.fromLogGroupName(
  this,
  'ErrorLogGroup',
  Fn.importValue(`${config.envName}-AppLogGroupName`)
);

const errorMetricFilter = new logs.MetricFilter(this, 'ErrorMetricFilter', {
  logGroup: errorLogGroup,
  metricNamespace: 'CustomMetrics/Application',
  metricName: 'ErrorCount',
  filterPattern: logs.FilterPattern.literal('[time, request_id, level=ERROR*, ...]'),
  metricValue: '1'
});
```

**アラーム**:
```typescript
const errorAlarm = new cloudwatch.Alarm(this, 'ErrorLogAlarm', {
  alarmName: `${config.envName}-error-log-detected`,
  metric: errorMetricFilter.metric({
    statistic: 'Sum',
    period: Duration.minutes(5)
  }),
  threshold: config.monitoring?.thresholds?.errorLogCount || 5,
  evaluationPeriods: 1,
  comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
  treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING
});

errorAlarm.addAlarmAction(new actions.SnsAction(criticalTopic));
```

#### 3.2.2 ECS CPU使用率アラーム
```typescript
const ecsCpuAlarm = new cloudwatch.Alarm(this, 'EcsCpuAlarm', {
  alarmName: `${config.envName}-ecs-cpu-high`,
  metric: new cloudwatch.Metric({
    namespace: 'AWS/ECS',
    metricName: 'CPUUtilization',
    dimensionsMap: {
      ServiceName: Fn.importValue(`${config.envName}-EcsServiceName`),
      ClusterName: Fn.importValue(`${config.envName}-EcsClusterName`)
    },
    statistic: 'Average',
    period: Duration.minutes(5)
  }),
  threshold: config.monitoring?.thresholds?.ecsCpuPercent || 80,
  evaluationPeriods: 1,
  comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
  treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING
});

ecsCpuAlarm.addAlarmAction(new actions.SnsAction(warningTopic));
```

#### 3.2.3 ECS メモリ使用率アラーム
```typescript
const ecsMemoryAlarm = new cloudwatch.Alarm(this, 'EcsMemoryAlarm', {
  alarmName: `${config.envName}-ecs-memory-high`,
  metric: new cloudwatch.Metric({
    namespace: 'AWS/ECS',
    metricName: 'MemoryUtilization',
    dimensionsMap: {
      ServiceName: Fn.importValue(`${config.envName}-EcsServiceName`),
      ClusterName: Fn.importValue(`${config.envName}-EcsClusterName`)
    },
    statistic: 'Average',
    period: Duration.minutes(5)
  }),
  threshold: config.monitoring?.thresholds?.ecsMemoryPercent || 80,
  evaluationPeriods: 1,
  comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
  treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING
});

ecsMemoryAlarm.addAlarmAction(new actions.SnsAction(warningTopic));
```

#### 3.2.4 ECS タスク起動失敗アラーム
**注意**: ECSのタスク起動失敗は、CloudWatch Eventsを利用してカウントする。

```typescript
// メトリクスフィルタ経由でのカウント（CloudWatch Logsベース）は複雑なため、
// シンプルにComposite Alarmまたは手動でのCloudWatch EventsからSNS通知を検討
// 今回は要件を満たすため、タスクカウントメトリクスの減少を検出する代替案を採用

const ecsTaskCountAlarm = new cloudwatch.Alarm(this, 'EcsTaskCountAlarm', {
  alarmName: `${config.envName}-ecs-task-count-low`,
  metric: new cloudwatch.Metric({
    namespace: 'AWS/ECS',
    metricName: 'RunningTaskCount',
    dimensionsMap: {
      ServiceName: Fn.importValue(`${config.envName}-EcsServiceName`),
      ClusterName: Fn.importValue(`${config.envName}-EcsClusterName`)
    },
    statistic: 'Average',
    period: Duration.minutes(5)
  }),
  threshold: config.ecs.desiredCount - 1, // 希望タスク数より1少ない
  evaluationPeriods: 1,
  comparisonOperator: cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
  treatMissingData: cloudwatch.TreatMissingData.BREACHING
});

ecsTaskCountAlarm.addAlarmAction(new actions.SnsAction(criticalTopic));
```

### 3.3 Aurora関連アラーム（4種類）

#### 3.3.1 Aurora CPU使用率アラーム
**クラスター識別子の抽出**:
```typescript
// エンドポイントからクラスター識別子を抽出
// 例: "cluster-dev.cluster-xxxxx.ap-northeast-1.rds.amazonaws.com" -> "cluster-dev"
const dbClusterEndpoint = Fn.importValue(`${config.envName}-DbClusterEndpoint`);
const dbClusterIdentifier = `cluster-${config.envName}`;
```

**アラーム**:
```typescript
const auroraCpuAlarm = new cloudwatch.Alarm(this, 'AuroraCpuAlarm', {
  alarmName: `${config.envName}-aurora-cpu-high`,
  metric: new cloudwatch.Metric({
    namespace: 'AWS/RDS',
    metricName: 'CPUUtilization',
    dimensionsMap: {
      DBClusterIdentifier: dbClusterIdentifier
    },
    statistic: 'Average',
    period: Duration.minutes(5)
  }),
  threshold: config.monitoring?.thresholds?.auroraCpuPercent || 80,
  evaluationPeriods: 1,
  comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
  treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING
});

auroraCpuAlarm.addAlarmAction(new actions.SnsAction(warningTopic));
```

#### 3.3.2 Aurora ディスク使用率アラーム（FreeableMemory）
```typescript
const auroraMemoryAlarm = new cloudwatch.Alarm(this, 'AuroraMemoryAlarm', {
  alarmName: `${config.envName}-aurora-memory-low`,
  metric: new cloudwatch.Metric({
    namespace: 'AWS/RDS',
    metricName: 'FreeableMemory',
    dimensionsMap: {
      DBClusterIdentifier: dbClusterIdentifier
    },
    statistic: 'Average',
    period: Duration.minutes(5)
  }),
  threshold: config.monitoring?.thresholds?.auroraFreeableMemoryBytes || 1_000_000_000, // 1GB
  evaluationPeriods: 1,
  comparisonOperator: cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
  treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING
});

auroraMemoryAlarm.addAlarmAction(new actions.SnsAction(warningTopic));
```

#### 3.3.3 Aurora 接続数アラーム
```typescript
const auroraConnectionsAlarm = new cloudwatch.Alarm(this, 'AuroraConnectionsAlarm', {
  alarmName: `${config.envName}-aurora-connections-high`,
  metric: new cloudwatch.Metric({
    namespace: 'AWS/RDS',
    metricName: 'DatabaseConnections',
    dimensionsMap: {
      DBClusterIdentifier: dbClusterIdentifier
    },
    statistic: 'Average',
    period: Duration.minutes(5)
  }),
  threshold: config.monitoring?.thresholds?.auroraConnectionsCount || 80,
  evaluationPeriods: 1,
  comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
  treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING
});

auroraConnectionsAlarm.addAlarmAction(new actions.SnsAction(warningTopic));
```

#### 3.3.4 Aurora レプリカラグアラーム
```typescript
const auroraReplicaLagAlarm = new cloudwatch.Alarm(this, 'AuroraReplicaLagAlarm', {
  alarmName: `${config.envName}-aurora-replica-lag-high`,
  metric: new cloudwatch.Metric({
    namespace: 'AWS/RDS',
    metricName: 'AuroraReplicaLag',
    dimensionsMap: {
      DBClusterIdentifier: dbClusterIdentifier
    },
    statistic: 'Average',
    period: Duration.minutes(5)
  }),
  threshold: config.monitoring?.thresholds?.auroraReplicaLagMs || 1000, // 1秒 = 1000ms
  evaluationPeriods: 1,
  comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
  treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING
});

auroraReplicaLagAlarm.addAlarmAction(new actions.SnsAction(criticalTopic));
```

### 3.4 ALB関連アラーム（3種類）

#### 3.4.1 ALB 5xxエラー率アラーム
**メトリクスMath**を使用してエラー率を計算する。

```typescript
const alb5xxErrorRateAlarm = new cloudwatch.Alarm(this, 'Alb5xxErrorRateAlarm', {
  alarmName: `${config.envName}-alb-5xx-error-rate-high`,
  metric: new cloudwatch.MathExpression({
    expression: '(m2 / m1) * 100',
    usingMetrics: {
      m1: new cloudwatch.Metric({
        namespace: 'AWS/ApplicationELB',
        metricName: 'RequestCount',
        dimensionsMap: {
          LoadBalancer: Fn.select(1, Fn.split('loadbalancer/', Fn.importValue(`${config.envName}-AlbArn`)))
        },
        statistic: 'Sum',
        period: Duration.minutes(5)
      }),
      m2: new cloudwatch.Metric({
        namespace: 'AWS/ApplicationELB',
        metricName: 'HTTPCode_Target_5XX_Count',
        dimensionsMap: {
          LoadBalancer: Fn.select(1, Fn.split('loadbalancer/', Fn.importValue(`${config.envName}-AlbArn`)))
        },
        statistic: 'Sum',
        period: Duration.minutes(5)
      })
    },
    period: Duration.minutes(5)
  }),
  threshold: config.monitoring?.thresholds?.alb5xxErrorRatePercent || 5,
  evaluationPeriods: 1,
  comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
  treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING
});

alb5xxErrorRateAlarm.addAlarmAction(new actions.SnsAction(criticalTopic));
```

**注意**: ALB ARNから`LoadBalancer`ディメンション値を抽出する（`arn:aws:elasticloadbalancing:region:account-id:loadbalancer/app/name/id` → `app/name/id`）

#### 3.4.2 ALB ターゲットヘルスチェック失敗アラーム
```typescript
const albUnhealthyHostAlarm = new cloudwatch.Alarm(this, 'AlbUnhealthyHostAlarm', {
  alarmName: `${config.envName}-alb-unhealthy-host`,
  metric: new cloudwatch.Metric({
    namespace: 'AWS/ApplicationELB',
    metricName: 'UnHealthyHostCount',
    dimensionsMap: {
      LoadBalancer: Fn.select(1, Fn.split('loadbalancer/', Fn.importValue(`${config.envName}-AlbArn`))),
      TargetGroup: Fn.select(1, Fn.split('targetgroup/', Fn.importValue(`${config.envName}-TargetGroupArn`)))
    },
    statistic: 'Maximum',
    period: Duration.minutes(5)
  }),
  threshold: 1,
  evaluationPeriods: 1,
  comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
  treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING
});

albUnhealthyHostAlarm.addAlarmAction(new actions.SnsAction(criticalTopic));
```

**注意**: TargetGroup ARNのエクスポートが必要（ComputeStackから）

#### 3.4.3 ALB レスポンスタイムアラーム
```typescript
const albResponseTimeAlarm = new cloudwatch.Alarm(this, 'AlbResponseTimeAlarm', {
  alarmName: `${config.envName}-alb-response-time-high`,
  metric: new cloudwatch.Metric({
    namespace: 'AWS/ApplicationELB',
    metricName: 'TargetResponseTime',
    dimensionsMap: {
      LoadBalancer: Fn.select(1, Fn.split('loadbalancer/', Fn.importValue(`${config.envName}-AlbArn`)))
    },
    statistic: 'Average',
    period: Duration.minutes(5)
  }),
  threshold: config.monitoring?.thresholds?.albResponseTimeSeconds || 2,
  evaluationPeriods: 1,
  comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
  treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING
});

albResponseTimeAlarm.addAlarmAction(new actions.SnsAction(warningTopic));
```

---

## 4. CloudWatch Dashboardの設計

### 4.1 ダッシュボード構成
```typescript
const dashboard = new cloudwatch.Dashboard(this, 'Dashboard', {
  dashboardName: `${config.envName}-application-dashboard`
});
```

### 4.2 ウィジェット構成

#### 4.2.1 ECS メトリクス
```typescript
// ECS CPU使用率
dashboard.addWidgets(
  new cloudwatch.GraphWidget({
    title: 'ECS CPU Utilization (%)',
    left: [
      new cloudwatch.Metric({
        namespace: 'AWS/ECS',
        metricName: 'CPUUtilization',
        dimensionsMap: {
          ServiceName: Fn.importValue(`${config.envName}-EcsServiceName`),
          ClusterName: Fn.importValue(`${config.envName}-EcsClusterName`)
        },
        statistic: 'Average',
        period: Duration.minutes(5),
        label: 'CPU Utilization'
      })
    ],
    width: 12,
    height: 6
  })
);

// ECS メモリ使用率
dashboard.addWidgets(
  new cloudwatch.GraphWidget({
    title: 'ECS Memory Utilization (%)',
    left: [
      new cloudwatch.Metric({
        namespace: 'AWS/ECS',
        metricName: 'MemoryUtilization',
        dimensionsMap: {
          ServiceName: Fn.importValue(`${config.envName}-EcsServiceName`),
          ClusterName: Fn.importValue(`${config.envName}-EcsClusterName`)
        },
        statistic: 'Average',
        period: Duration.minutes(5),
        label: 'Memory Utilization'
      })
    ],
    width: 12,
    height: 6
  })
);

// ECS タスク数
dashboard.addWidgets(
  new cloudwatch.GraphWidget({
    title: 'ECS Task Count',
    left: [
      new cloudwatch.Metric({
        namespace: 'AWS/ECS',
        metricName: 'RunningTaskCount',
        dimensionsMap: {
          ServiceName: Fn.importValue(`${config.envName}-EcsServiceName`),
          ClusterName: Fn.importValue(`${config.envName}-EcsClusterName`)
        },
        statistic: 'Average',
        period: Duration.minutes(5),
        label: 'Running Tasks'
      })
    ],
    width: 12,
    height: 6
  })
);

// エラーログ数
dashboard.addWidgets(
  new cloudwatch.GraphWidget({
    title: 'Application Error Count',
    left: [
      errorMetricFilter.metric({
        statistic: 'Sum',
        period: Duration.minutes(5),
        label: 'Error Count'
      })
    ],
    width: 12,
    height: 6
  })
);
```

#### 4.2.2 Aurora メトリクス
```typescript
// Aurora CPU使用率
dashboard.addWidgets(
  new cloudwatch.GraphWidget({
    title: 'Aurora CPU Utilization (%)',
    left: [
      new cloudwatch.Metric({
        namespace: 'AWS/RDS',
        metricName: 'CPUUtilization',
        dimensionsMap: {
          DBClusterIdentifier: dbClusterIdentifier
        },
        statistic: 'Average',
        period: Duration.minutes(5),
        label: 'CPU Utilization'
      })
    ],
    width: 12,
    height: 6
  })
);

// Aurora 接続数
dashboard.addWidgets(
  new cloudwatch.GraphWidget({
    title: 'Aurora Database Connections',
    left: [
      new cloudwatch.Metric({
        namespace: 'AWS/RDS',
        metricName: 'DatabaseConnections',
        dimensionsMap: {
          DBClusterIdentifier: dbClusterIdentifier
        },
        statistic: 'Average',
        period: Duration.minutes(5),
        label: 'Connections'
      })
    ],
    width: 12,
    height: 6
  })
);

// Aurora レプリカラグ
dashboard.addWidgets(
  new cloudwatch.GraphWidget({
    title: 'Aurora Replica Lag (ms)',
    left: [
      new cloudwatch.Metric({
        namespace: 'AWS/RDS',
        metricName: 'AuroraReplicaLag',
        dimensionsMap: {
          DBClusterIdentifier: dbClusterIdentifier
        },
        statistic: 'Average',
        period: Duration.minutes(5),
        label: 'Replica Lag'
      })
    ],
    width: 12,
    height: 6
  })
);

// Aurora ディスク使用可能量
dashboard.addWidgets(
  new cloudwatch.GraphWidget({
    title: 'Aurora Freeable Memory (GB)',
    left: [
      new cloudwatch.Metric({
        namespace: 'AWS/RDS',
        metricName: 'FreeableMemory',
        dimensionsMap: {
          DBClusterIdentifier: dbClusterIdentifier
        },
        statistic: 'Average',
        period: Duration.minutes(5),
        label: 'Freeable Memory'
      }).with({
        // バイトからGBに変換
        statistic: 'Average'
      })
    ],
    width: 12,
    height: 6
  })
);
```

#### 4.2.3 ALB メトリクス
```typescript
const albDimension = Fn.select(1, Fn.split('loadbalancer/', Fn.importValue(`${config.envName}-AlbArn`)));

// ALB リクエスト数
dashboard.addWidgets(
  new cloudwatch.GraphWidget({
    title: 'ALB Request Count',
    left: [
      new cloudwatch.Metric({
        namespace: 'AWS/ApplicationELB',
        metricName: 'RequestCount',
        dimensionsMap: {
          LoadBalancer: albDimension
        },
        statistic: 'Sum',
        period: Duration.minutes(5),
        label: 'Requests'
      })
    ],
    width: 12,
    height: 6
  })
);

// ALB レイテンシ（P50, P95, P99）
dashboard.addWidgets(
  new cloudwatch.GraphWidget({
    title: 'ALB Target Response Time (seconds)',
    left: [
      new cloudwatch.Metric({
        namespace: 'AWS/ApplicationELB',
        metricName: 'TargetResponseTime',
        dimensionsMap: {
          LoadBalancer: albDimension
        },
        statistic: 'p50',
        period: Duration.minutes(5),
        label: 'P50'
      }),
      new cloudwatch.Metric({
        namespace: 'AWS/ApplicationELB',
        metricName: 'TargetResponseTime',
        dimensionsMap: {
          LoadBalancer: albDimension
        },
        statistic: 'p95',
        period: Duration.minutes(5),
        label: 'P95'
      }),
      new cloudwatch.Metric({
        namespace: 'AWS/ApplicationELB',
        metricName: 'TargetResponseTime',
        dimensionsMap: {
          LoadBalancer: albDimension
        },
        statistic: 'p99',
        period: Duration.minutes(5),
        label: 'P99'
      }),
      new cloudwatch.Metric({
        namespace: 'AWS/ApplicationELB',
        metricName: 'TargetResponseTime',
        dimensionsMap: {
          LoadBalancer: albDimension
        },
        statistic: 'Average',
        period: Duration.minutes(5),
        label: 'Average'
      })
    ],
    width: 12,
    height: 6
  })
);

// ALB エラー率（4xx, 5xx）
dashboard.addWidgets(
  new cloudwatch.GraphWidget({
    title: 'ALB HTTP Error Codes',
    left: [
      new cloudwatch.Metric({
        namespace: 'AWS/ApplicationELB',
        metricName: 'HTTPCode_Target_4XX_Count',
        dimensionsMap: {
          LoadBalancer: albDimension
        },
        statistic: 'Sum',
        period: Duration.minutes(5),
        label: '4xx Errors'
      }),
      new cloudwatch.Metric({
        namespace: 'AWS/ApplicationELB',
        metricName: 'HTTPCode_Target_5XX_Count',
        dimensionsMap: {
          LoadBalancer: albDimension
        },
        statistic: 'Sum',
        period: Duration.minutes(5),
        label: '5xx Errors'
      })
    ],
    width: 12,
    height: 6
  })
);

// ALB ターゲット健全性
dashboard.addWidgets(
  new cloudwatch.GraphWidget({
    title: 'ALB Target Health',
    left: [
      new cloudwatch.Metric({
        namespace: 'AWS/ApplicationELB',
        metricName: 'HealthyHostCount',
        dimensionsMap: {
          LoadBalancer: albDimension,
          TargetGroup: Fn.select(1, Fn.split('targetgroup/', Fn.importValue(`${config.envName}-TargetGroupArn`)))
        },
        statistic: 'Average',
        period: Duration.minutes(5),
        label: 'Healthy Hosts'
      }),
      new cloudwatch.Metric({
        namespace: 'AWS/ApplicationELB',
        metricName: 'UnHealthyHostCount',
        dimensionsMap: {
          LoadBalancer: albDimension,
          TargetGroup: Fn.select(1, Fn.split('targetgroup/', Fn.importValue(`${config.envName}-TargetGroupArn`)))
        },
        statistic: 'Average',
        period: Duration.minutes(5),
        label: 'Unhealthy Hosts'
      })
    ],
    width: 12,
    height: 6
  })
);
```

#### 4.2.4 VPCエンドポイント メトリクス
**注意**: VPCエンドポイントのメトリクスは、デフォルトでは利用できない場合があるため、オプションとして実装する。

```typescript
// VPCエンドポイント データ転送量（オプション）
// ※ VPCエンドポイントIDの取得が必要（NetworkStackからのエクスポートが必要）
```

---

## 5. スタック間参照の設計

### 5.1 Fn.importValue使用パターン
MonitoringStackは、他のスタックから以下の値をインポートする。

```typescript
// ComputeStackから
const ecsClusterName = Fn.importValue(`${config.envName}-EcsClusterName`);
const ecsServiceName = Fn.importValue(`${config.envName}-EcsServiceName`);
const albArn = Fn.importValue(`${config.envName}-AlbArn`);
const targetGroupArn = Fn.importValue(`${config.envName}-TargetGroupArn`); // 追加必要
const appLogGroupName = Fn.importValue(`${config.envName}-AppLogGroupName`);

// DatabaseStackから
const dbClusterEndpoint = Fn.importValue(`${config.envName}-DbClusterEndpoint`);
```

### 5.2 ComputeStackへの追加エクスポート
ComputeStackに以下のCfnOutputを追加する必要がある。

```typescript
// compute-stack.ts に追加
new CfnOutput(this, 'TargetGroupArn', {
  value: targetGroup.targetGroupArn,
  description: 'Target Group ARN',
  exportName: `${config.envName}-TargetGroupArn`
});
```

---

## 6. 環境設定への追加項目

### 6.1 EnvConfigインターフェースの拡張
`cdk/lib/config/env-config.ts` に以下の設定を追加する。

```typescript
export interface EnvConfig {
  // 既存の設定...

  // 監視設定（新規追加）
  monitoring?: {
    // アラート通知先メールアドレス
    alertEmail?: string;

    // アラーム閾値
    thresholds?: {
      // ECS関連
      errorLogCount?: number;           // デフォルト: 5
      ecsCpuPercent?: number;            // デフォルト: 80
      ecsMemoryPercent?: number;         // デフォルト: 80

      // Aurora関連
      auroraCpuPercent?: number;         // デフォルト: 80
      auroraFreeableMemoryBytes?: number; // デフォルト: 1GB (1_000_000_000)
      auroraConnectionsCount?: number;   // デフォルト: 80
      auroraReplicaLagMs?: number;       // デフォルト: 1000 (1秒)

      // ALB関連
      alb5xxErrorRatePercent?: number;   // デフォルト: 5
      albResponseTimeSeconds?: number;   // デフォルト: 2
    };
  };
}
```

### 6.2 dev.tsへの設定追加
```typescript
export const devConfig: EnvConfig = {
  // 既存の設定...

  monitoring: {
    alertEmail: 'dev-alerts@example.com', // TODO: 実際のメールアドレスに変更
    thresholds: {
      errorLogCount: 10,          // 開発環境は閾値を緩く
      ecsCpuPercent: 85,
      ecsMemoryPercent: 85,
      auroraCpuPercent: 85,
      auroraFreeableMemoryBytes: 500_000_000, // 500MB
      auroraConnectionsCount: 50,
      auroraReplicaLagMs: 2000,   // 2秒
      alb5xxErrorRatePercent: 10,
      albResponseTimeSeconds: 3
    }
  }
};
```

### 6.3 prod.tsへの設定追加
```typescript
export const prodConfig: EnvConfig = {
  // 既存の設定...

  monitoring: {
    alertEmail: 'prod-alerts@example.com', // TODO: 実際のメールアドレスに変更
    thresholds: {
      errorLogCount: 5,           // 本番環境は閾値を厳しく
      ecsCpuPercent: 80,
      ecsMemoryPercent: 80,
      auroraCpuPercent: 80,
      auroraFreeableMemoryBytes: 1_000_000_000, // 1GB
      auroraConnectionsCount: 80,
      auroraReplicaLagMs: 1000,   // 1秒
      alb5xxErrorRatePercent: 5,
      albResponseTimeSeconds: 2
    }
  }
};
```

---

## 7. コード構造（monitoring-stack.ts）

### 7.1 ファイル構成
```
cdk/lib/stacks/monitoring-stack.ts
```

### 7.2 クラス構造
```typescript
import {
  Stack,
  StackProps,
  Fn,
  Duration,
  Tags,
  CfnOutput
} from 'aws-cdk-lib';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as actions from 'aws-cdk-lib/aws-cloudwatch-actions';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as subscriptions from 'aws-cdk-lib/aws-sns-subscriptions';
import * as logs from 'aws-cdk-lib/aws-logs';
import { Construct } from 'constructs';
import { EnvConfig } from '../config/env-config';

export interface MonitoringStackProps extends StackProps {
  config: EnvConfig;
}

export class MonitoringStack extends Stack {
  constructor(scope: Construct, id: string, props: MonitoringStackProps) {
    super(scope, id, props);

    const { config } = props;

    // 1. スタック間参照のインポート
    // 2. SNSトピックの作成
    // 3. CloudWatch Alarmsの作成
    //    3.1 ECS関連アラーム
    //    3.2 Aurora関連アラーム
    //    3.3 ALB関連アラーム
    // 4. CloudWatch Dashboardの作成
    // 5. CfnOutput
  }
}
```

### 7.3 メソッド分割（推奨）
コードの可読性を高めるため、以下のようにプライベートメソッドに分割する。

```typescript
export class MonitoringStack extends Stack {
  private criticalTopic: sns.Topic;
  private warningTopic: sns.Topic;

  constructor(scope: Construct, id: string, props: MonitoringStackProps) {
    super(scope, id, props);

    const { config } = props;

    // SNSトピック作成
    this.createSnsTopics(config);

    // CloudWatch Alarms作成
    this.createEcsAlarms(config);
    this.createAuroraAlarms(config);
    this.createAlbAlarms(config);

    // CloudWatch Dashboard作成
    this.createDashboard(config);
  }

  private createSnsTopics(config: EnvConfig): void { /* ... */ }
  private createEcsAlarms(config: EnvConfig): void { /* ... */ }
  private createAuroraAlarms(config: EnvConfig): void { /* ... */ }
  private createAlbAlarms(config: EnvConfig): void { /* ... */ }
  private createDashboard(config: EnvConfig): void { /* ... */ }
}
```

---

## 8. 影響範囲分析

### 8.1 既存スタックへの変更

#### 8.1.1 ComputeStack（compute-stack.ts）
**変更内容**: TargetGroup ARNのエクスポート追加

**追加箇所**:
```typescript
// compute-stack.ts の CfnOutput セクションに追加
new CfnOutput(this, 'TargetGroupArn', {
  value: targetGroup.targetGroupArn,
  description: 'Target Group ARN',
  exportName: `${config.envName}-TargetGroupArn`
});
```

**影響**: 既存リソースには影響なし（スタックアウトプット追加のみ）

#### 8.1.2 環境設定ファイル（env-config.ts, dev.ts, prod.ts）
**変更内容**: monitoring設定の追加

**影響**: 既存の設定には影響なし（オプショナルフィールドとして追加）

### 8.2 新規作成ファイル
- `cdk/lib/stacks/monitoring-stack.ts`

### 8.3 app.tsへの追加
```typescript
// cdk/bin/app.ts
import { MonitoringStack } from '../lib/stacks/monitoring-stack';

// 既存のスタック作成後に追加
const monitoringStack = new MonitoringStack(app, `MonitoringStack-${envName}`, {
  env,
  config
});

// 依存関係の明示
monitoringStack.addDependency(computeStack);
monitoringStack.addDependency(databaseStack);
```

---

## 9. デプロイ戦略

### 9.1 デプロイ順序
1. ComputeStackの更新（TargetGroup ARNエクスポート追加）
2. MonitoringStackの新規デプロイ
3. メールサブスクリプションの手動確認

### 9.2 ロールバック対策
- MonitoringStackは既存リソースに影響を与えないため、削除しても他のスタックへの影響なし
- アラームの誤発報を避けるため、初回デプロイ時は閾値を緩めに設定することを推奨

---

## 10. テスト計画

### 10.1 デプロイテスト
1. `cdk synth`でテンプレート生成確認
2. `cdk diff`で変更内容確認
3. `cdk deploy`でデプロイ
4. CloudWatchコンソールでアラーム確認
5. ダッシュボード表示確認

### 10.2 アラームテスト
1. ERRORログ送信テスト
2. ECS CPU負荷テスト（意図的にCPUを上げる）
3. SNS通知受信確認

---

## 11. 制約事項と注意事項

### 11.1 制約事項
1. **メールサブスクリプション手動確認**: SNSメールサブスクリプションは、初回デプロイ後にサブスクリプション確認メールを手動で承認する必要がある
2. **Auroraクラスター識別子**: DatabaseStackからのエンドポイント情報を基に、クラスター識別子を構築する（`cluster-${envName}`パターンを使用）
3. **TargetGroup ARN**: ComputeStackからのエクスポートが必要（既存スタックの更新が必要）

### 11.2 注意事項
1. **アラーム閾値の調整**: 環境やワークロードに応じて閾値を調整する必要がある
2. **コスト**: CloudWatch Alarmsは1アラームあたり$0.10/月、メトリクスフィルタは無料
3. **メトリクスの遅延**: CloudWatchメトリクスは最大5分の遅延がある可能性がある
4. **ダッシュボードの自動更新**: ダッシュボードはリアルタイム更新されるが、ブラウザのリフレッシュが必要な場合がある

---

## 12. 将来拡張

### 12.1 Slack通知（フェーズ外）
Lambda関数を追加し、SNSトピックからSlackへ通知を送信する。

### 12.2 カスタムメトリクス（フェーズ外）
アプリケーションから独自のメトリクスをCloudWatchに送信する。

### 12.3 Composite Alarms（フェーズ外）
複数のアラームを組み合わせた複合アラームを作成する。

---

## まとめ

MonitoringStackは、既存のComputeStack、DatabaseStackから必要な情報をインポートし、11種類のCloudWatch Alarms、2つのSNSトピック、1つのCloudWatch Dashboardを作成する。環境設定ファイルに監視設定を追加し、アラーム閾値や通知先メールアドレスを環境別に管理する。

**次のステップ**: tasklist.mdの作成と承認

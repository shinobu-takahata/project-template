import {
  Stack,
  StackProps,
  Fn,
  Duration,
  Tags,
  CfnOutput,
} from "aws-cdk-lib";
import * as cloudwatch from "aws-cdk-lib/aws-cloudwatch";
import * as actions from "aws-cdk-lib/aws-cloudwatch-actions";
import * as sns from "aws-cdk-lib/aws-sns";
import * as subscriptions from "aws-cdk-lib/aws-sns-subscriptions";
import * as logs from "aws-cdk-lib/aws-logs";
import { Construct } from "constructs";
import { EnvConfig } from "../config/env-config";

export interface MonitoringStackProps extends StackProps {
  config: EnvConfig;
}

export class MonitoringStack extends Stack {
  private criticalTopic: sns.Topic;
  private warningTopic: sns.Topic;
  private errorMetricFilter: logs.MetricFilter;

  constructor(scope: Construct, id: string, props: MonitoringStackProps) {
    super(scope, id, props);

    const { config } = props;

    // =========================================
    // 1. スタック間参照のインポート
    // =========================================
    const ecsClusterName = Fn.importValue(`${config.envName}-EcsClusterName`);
    const ecsServiceName = Fn.importValue(`${config.envName}-EcsServiceName`);
    const albArn = Fn.importValue(`${config.envName}-AlbArn`);
    const targetGroupArn = Fn.importValue(`${config.envName}-TargetGroupArn`);
    const errorLogGroupName = Fn.importValue(
      `${config.envName}-ErrorLogGroupName`
    );

    // Auroraクラスター識別子（命名規則に基づく）
    const dbClusterIdentifier = `cluster-${config.envName}`;

    // ALB ARNからLoadBalancerディメンションを抽出
    // arn:aws:elasticloadbalancing:region:account:loadbalancer/app/name/id -> app/name/id
    const albDimension = Fn.select(
      1,
      Fn.split("loadbalancer/", albArn)
    );

    // TargetGroup ARNからTargetGroupディメンションを抽出
    const targetGroupDimension = Fn.select(
      1,
      Fn.split("targetgroup/", targetGroupArn)
    );

    // =========================================
    // 2. SNSトピックの作成
    // =========================================
    this.createSnsTopics(config);

    // =========================================
    // 3. CloudWatch Alarmsの作成
    // =========================================
    this.createEcsAlarms(
      config,
      ecsClusterName,
      ecsServiceName,
      errorLogGroupName
    );
    this.createAuroraAlarms(config, dbClusterIdentifier);
    this.createAlbAlarms(config, albDimension, targetGroupDimension);

    // =========================================
    // 4. CloudWatch Dashboardの作成
    // =========================================
    this.createDashboard(
      config,
      ecsClusterName,
      ecsServiceName,
      dbClusterIdentifier,
      albDimension,
      targetGroupDimension
    );

    // =========================================
    // 5. CfnOutput
    // =========================================
    new CfnOutput(this, "CriticalAlertsTopicArn", {
      value: this.criticalTopic.topicArn,
      description: "Critical Alerts SNS Topic ARN",
      exportName: `${config.envName}-CriticalAlertsTopicArn`,
    });

    new CfnOutput(this, "WarningAlertsTopicArn", {
      value: this.warningTopic.topicArn,
      description: "Warning Alerts SNS Topic ARN",
      exportName: `${config.envName}-WarningAlertsTopicArn`,
    });
  }

  /**
   * SNSトピックの作成
   */
  private createSnsTopics(config: EnvConfig): void {
    // Critical Alerts トピック
    this.criticalTopic = new sns.Topic(this, "CriticalAlertsTopic", {
      topicName: `critical-alerts-${config.envName}`,
      displayName: "Critical Alerts",
    });

    Tags.of(this.criticalTopic).add("Environment", config.envName);
    Tags.of(this.criticalTopic).add("Project", "project-template");
    Tags.of(this.criticalTopic).add("ManagedBy", "CDK");

    // Warning Alerts トピック
    this.warningTopic = new sns.Topic(this, "WarningAlertsTopic", {
      topicName: `warning-alerts-${config.envName}`,
      displayName: "Warning Alerts",
    });

    Tags.of(this.warningTopic).add("Environment", config.envName);
    Tags.of(this.warningTopic).add("Project", "project-template");
    Tags.of(this.warningTopic).add("ManagedBy", "CDK");

    // メールサブスクリプションの追加
    if (config.monitoring?.alertEmail) {
      this.criticalTopic.addSubscription(
        new subscriptions.EmailSubscription(config.monitoring.alertEmail)
      );

      this.warningTopic.addSubscription(
        new subscriptions.EmailSubscription(config.monitoring.alertEmail)
      );
    }
  }

  /**
   * ECS関連アラームの作成
   */
  private createEcsAlarms(
    config: EnvConfig,
    ecsClusterName: string,
    ecsServiceName: string,
    errorLogGroupName: string
  ): void {
    // エラーログロググループの参照
    const errorLogGroup = logs.LogGroup.fromLogGroupName(
      this,
      "ErrorLogGroup",
      errorLogGroupName
    );

    // ERRORログ検出用メトリクスフィルタ
    this.errorMetricFilter = new logs.MetricFilter(this, "ErrorMetricFilter", {
      logGroup: errorLogGroup,
      metricNamespace: "CustomMetrics/Application",
      metricName: "ErrorCount",
      filterPattern: logs.FilterPattern.anyTerm("ERROR", "CRITICAL", "FATAL"),
      metricValue: "1",
    });

    // ERRORログ検出アラーム
    const errorAlarm = new cloudwatch.Alarm(this, "ErrorLogAlarm", {
      alarmName: `${config.envName}-error-log-detected`,
      alarmDescription: "Application error logs detected",
      metric: this.errorMetricFilter.metric({
        statistic: "Sum",
        period: Duration.minutes(5),
      }),
      threshold: config.monitoring?.thresholds?.errorLogCount ?? 5,
      evaluationPeriods: 1,
      comparisonOperator:
        cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });
    errorAlarm.addAlarmAction(new actions.SnsAction(this.criticalTopic));

    // ECS CPU使用率アラーム
    const ecsCpuAlarm = new cloudwatch.Alarm(this, "EcsCpuAlarm", {
      alarmName: `${config.envName}-ecs-cpu-high`,
      alarmDescription: "ECS CPU utilization is high",
      metric: new cloudwatch.Metric({
        namespace: "AWS/ECS",
        metricName: "CPUUtilization",
        dimensionsMap: {
          ServiceName: ecsServiceName,
          ClusterName: ecsClusterName,
        },
        statistic: "Average",
        period: Duration.minutes(5),
      }),
      threshold: config.monitoring?.thresholds?.ecsCpuPercent ?? 80,
      evaluationPeriods: 1,
      comparisonOperator:
        cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });
    ecsCpuAlarm.addAlarmAction(new actions.SnsAction(this.warningTopic));

    // ECS メモリ使用率アラーム
    const ecsMemoryAlarm = new cloudwatch.Alarm(this, "EcsMemoryAlarm", {
      alarmName: `${config.envName}-ecs-memory-high`,
      alarmDescription: "ECS memory utilization is high",
      metric: new cloudwatch.Metric({
        namespace: "AWS/ECS",
        metricName: "MemoryUtilization",
        dimensionsMap: {
          ServiceName: ecsServiceName,
          ClusterName: ecsClusterName,
        },
        statistic: "Average",
        period: Duration.minutes(5),
      }),
      threshold: config.monitoring?.thresholds?.ecsMemoryPercent ?? 80,
      evaluationPeriods: 1,
      comparisonOperator:
        cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });
    ecsMemoryAlarm.addAlarmAction(new actions.SnsAction(this.warningTopic));

    // ECS タスクカウント低下アラーム
    const ecsTaskCountAlarm = new cloudwatch.Alarm(this, "EcsTaskCountAlarm", {
      alarmName: `${config.envName}-ecs-task-count-low`,
      alarmDescription: "ECS running task count is below desired",
      metric: new cloudwatch.Metric({
        namespace: "AWS/ECS",
        metricName: "RunningTaskCount",
        dimensionsMap: {
          ServiceName: ecsServiceName,
          ClusterName: ecsClusterName,
        },
        statistic: "Average",
        period: Duration.minutes(5),
      }),
      threshold: config.ecs.desiredCount - 1,
      evaluationPeriods: 1,
      comparisonOperator:
        cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.BREACHING,
    });
    ecsTaskCountAlarm.addAlarmAction(new actions.SnsAction(this.criticalTopic));
  }

  /**
   * Aurora関連アラームの作成
   */
  private createAuroraAlarms(
    config: EnvConfig,
    dbClusterIdentifier: string
  ): void {
    // Aurora CPU使用率アラーム
    const auroraCpuAlarm = new cloudwatch.Alarm(this, "AuroraCpuAlarm", {
      alarmName: `${config.envName}-aurora-cpu-high`,
      alarmDescription: "Aurora CPU utilization is high",
      metric: new cloudwatch.Metric({
        namespace: "AWS/RDS",
        metricName: "CPUUtilization",
        dimensionsMap: {
          DBClusterIdentifier: dbClusterIdentifier,
        },
        statistic: "Average",
        period: Duration.minutes(5),
      }),
      threshold: config.monitoring?.thresholds?.auroraCpuPercent ?? 80,
      evaluationPeriods: 1,
      comparisonOperator:
        cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });
    auroraCpuAlarm.addAlarmAction(new actions.SnsAction(this.warningTopic));

    // Aurora FreeableMemoryアラーム
    const auroraMemoryAlarm = new cloudwatch.Alarm(this, "AuroraMemoryAlarm", {
      alarmName: `${config.envName}-aurora-memory-low`,
      alarmDescription: "Aurora freeable memory is low",
      metric: new cloudwatch.Metric({
        namespace: "AWS/RDS",
        metricName: "FreeableMemory",
        dimensionsMap: {
          DBClusterIdentifier: dbClusterIdentifier,
        },
        statistic: "Average",
        period: Duration.minutes(5),
      }),
      threshold:
        config.monitoring?.thresholds?.auroraFreeableMemoryBytes ?? 1_000_000_000,
      evaluationPeriods: 1,
      comparisonOperator:
        cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    });
    auroraMemoryAlarm.addAlarmAction(new actions.SnsAction(this.warningTopic));

    // Aurora 接続数アラーム
    const auroraConnectionsAlarm = new cloudwatch.Alarm(
      this,
      "AuroraConnectionsAlarm",
      {
        alarmName: `${config.envName}-aurora-connections-high`,
        alarmDescription: "Aurora database connections are high",
        metric: new cloudwatch.Metric({
          namespace: "AWS/RDS",
          metricName: "DatabaseConnections",
          dimensionsMap: {
            DBClusterIdentifier: dbClusterIdentifier,
          },
          statistic: "Average",
          period: Duration.minutes(5),
        }),
        threshold: config.monitoring?.thresholds?.auroraConnectionsCount ?? 80,
        evaluationPeriods: 1,
        comparisonOperator:
          cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
        treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
      }
    );
    auroraConnectionsAlarm.addAlarmAction(
      new actions.SnsAction(this.warningTopic)
    );

    // Aurora レプリカラグアラーム
    const auroraReplicaLagAlarm = new cloudwatch.Alarm(
      this,
      "AuroraReplicaLagAlarm",
      {
        alarmName: `${config.envName}-aurora-replica-lag-high`,
        alarmDescription: "Aurora replica lag is high",
        metric: new cloudwatch.Metric({
          namespace: "AWS/RDS",
          metricName: "AuroraReplicaLag",
          dimensionsMap: {
            DBClusterIdentifier: dbClusterIdentifier,
          },
          statistic: "Average",
          period: Duration.minutes(5),
        }),
        threshold: config.monitoring?.thresholds?.auroraReplicaLagMs ?? 1000,
        evaluationPeriods: 1,
        comparisonOperator:
          cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
      }
    );
    auroraReplicaLagAlarm.addAlarmAction(
      new actions.SnsAction(this.criticalTopic)
    );
  }

  /**
   * ALB関連アラームの作成
   */
  private createAlbAlarms(
    config: EnvConfig,
    albDimension: string,
    targetGroupDimension: string
  ): void {
    // ALB 5xxエラー率アラーム（メトリクスMath使用）
    const alb5xxErrorRateAlarm = new cloudwatch.Alarm(
      this,
      "Alb5xxErrorRateAlarm",
      {
        alarmName: `${config.envName}-alb-5xx-error-rate-high`,
        alarmDescription: "ALB 5xx error rate is high",
        metric: new cloudwatch.MathExpression({
          expression: "IF(m1 > 0, (m2 / m1) * 100, 0)",
          usingMetrics: {
            m1: new cloudwatch.Metric({
              namespace: "AWS/ApplicationELB",
              metricName: "RequestCount",
              dimensionsMap: {
                LoadBalancer: albDimension,
              },
              statistic: "Sum",
              period: Duration.minutes(5),
            }),
            m2: new cloudwatch.Metric({
              namespace: "AWS/ApplicationELB",
              metricName: "HTTPCode_Target_5XX_Count",
              dimensionsMap: {
                LoadBalancer: albDimension,
              },
              statistic: "Sum",
              period: Duration.minutes(5),
            }),
          },
          period: Duration.minutes(5),
        }),
        threshold: config.monitoring?.thresholds?.alb5xxErrorRatePercent ?? 5,
        evaluationPeriods: 1,
        comparisonOperator:
          cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
      }
    );
    alb5xxErrorRateAlarm.addAlarmAction(
      new actions.SnsAction(this.criticalTopic)
    );

    // ALB ターゲットヘルスチェック失敗アラーム
    const albUnhealthyHostAlarm = new cloudwatch.Alarm(
      this,
      "AlbUnhealthyHostAlarm",
      {
        alarmName: `${config.envName}-alb-unhealthy-host`,
        alarmDescription: "ALB has unhealthy targets",
        metric: new cloudwatch.Metric({
          namespace: "AWS/ApplicationELB",
          metricName: "UnHealthyHostCount",
          dimensionsMap: {
            LoadBalancer: albDimension,
            TargetGroup: targetGroupDimension,
          },
          statistic: "Maximum",
          period: Duration.minutes(5),
        }),
        threshold: 1,
        evaluationPeriods: 1,
        comparisonOperator:
          cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
        treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
      }
    );
    albUnhealthyHostAlarm.addAlarmAction(
      new actions.SnsAction(this.criticalTopic)
    );

    // ALB レスポンスタイムアラーム
    const albResponseTimeAlarm = new cloudwatch.Alarm(
      this,
      "AlbResponseTimeAlarm",
      {
        alarmName: `${config.envName}-alb-response-time-high`,
        alarmDescription: "ALB target response time is high",
        metric: new cloudwatch.Metric({
          namespace: "AWS/ApplicationELB",
          metricName: "TargetResponseTime",
          dimensionsMap: {
            LoadBalancer: albDimension,
          },
          statistic: "Average",
          period: Duration.minutes(5),
        }),
        threshold: config.monitoring?.thresholds?.albResponseTimeSeconds ?? 2,
        evaluationPeriods: 1,
        comparisonOperator:
          cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
      }
    );
    albResponseTimeAlarm.addAlarmAction(
      new actions.SnsAction(this.warningTopic)
    );
  }

  /**
   * CloudWatch Dashboardの作成
   */
  private createDashboard(
    config: EnvConfig,
    ecsClusterName: string,
    ecsServiceName: string,
    dbClusterIdentifier: string,
    albDimension: string,
    targetGroupDimension: string
  ): void {
    const dashboard = new cloudwatch.Dashboard(this, "Dashboard", {
      dashboardName: `${config.envName}-application-dashboard`,
    });

    // =========================================
    // ECS メトリクス
    // =========================================
    dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: "ECS CPU Utilization (%)",
        left: [
          new cloudwatch.Metric({
            namespace: "AWS/ECS",
            metricName: "CPUUtilization",
            dimensionsMap: {
              ServiceName: ecsServiceName,
              ClusterName: ecsClusterName,
            },
            statistic: "Average",
            period: Duration.minutes(5),
            label: "CPU Utilization",
          }),
        ],
        width: 12,
        height: 6,
      }),
      new cloudwatch.GraphWidget({
        title: "ECS Memory Utilization (%)",
        left: [
          new cloudwatch.Metric({
            namespace: "AWS/ECS",
            metricName: "MemoryUtilization",
            dimensionsMap: {
              ServiceName: ecsServiceName,
              ClusterName: ecsClusterName,
            },
            statistic: "Average",
            period: Duration.minutes(5),
            label: "Memory Utilization",
          }),
        ],
        width: 12,
        height: 6,
      })
    );

    dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: "ECS Task Count",
        left: [
          new cloudwatch.Metric({
            namespace: "AWS/ECS",
            metricName: "RunningTaskCount",
            dimensionsMap: {
              ServiceName: ecsServiceName,
              ClusterName: ecsClusterName,
            },
            statistic: "Average",
            period: Duration.minutes(5),
            label: "Running Tasks",
          }),
        ],
        width: 12,
        height: 6,
      }),
      new cloudwatch.GraphWidget({
        title: "Application Error Count",
        left: [
          this.errorMetricFilter.metric({
            statistic: "Sum",
            period: Duration.minutes(5),
            label: "Error Count",
          }),
        ],
        width: 12,
        height: 6,
      })
    );

    // =========================================
    // Aurora メトリクス
    // =========================================
    dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: "Aurora CPU Utilization (%)",
        left: [
          new cloudwatch.Metric({
            namespace: "AWS/RDS",
            metricName: "CPUUtilization",
            dimensionsMap: {
              DBClusterIdentifier: dbClusterIdentifier,
            },
            statistic: "Average",
            period: Duration.minutes(5),
            label: "CPU Utilization",
          }),
        ],
        width: 12,
        height: 6,
      }),
      new cloudwatch.GraphWidget({
        title: "Aurora Database Connections",
        left: [
          new cloudwatch.Metric({
            namespace: "AWS/RDS",
            metricName: "DatabaseConnections",
            dimensionsMap: {
              DBClusterIdentifier: dbClusterIdentifier,
            },
            statistic: "Average",
            period: Duration.minutes(5),
            label: "Connections",
          }),
        ],
        width: 12,
        height: 6,
      })
    );

    dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: "Aurora Replica Lag (ms)",
        left: [
          new cloudwatch.Metric({
            namespace: "AWS/RDS",
            metricName: "AuroraReplicaLag",
            dimensionsMap: {
              DBClusterIdentifier: dbClusterIdentifier,
            },
            statistic: "Average",
            period: Duration.minutes(5),
            label: "Replica Lag",
          }),
        ],
        width: 12,
        height: 6,
      }),
      new cloudwatch.GraphWidget({
        title: "Aurora Freeable Memory (bytes)",
        left: [
          new cloudwatch.Metric({
            namespace: "AWS/RDS",
            metricName: "FreeableMemory",
            dimensionsMap: {
              DBClusterIdentifier: dbClusterIdentifier,
            },
            statistic: "Average",
            period: Duration.minutes(5),
            label: "Freeable Memory",
          }),
        ],
        width: 12,
        height: 6,
      })
    );

    // =========================================
    // ALB メトリクス
    // =========================================
    dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: "ALB Request Count",
        left: [
          new cloudwatch.Metric({
            namespace: "AWS/ApplicationELB",
            metricName: "RequestCount",
            dimensionsMap: {
              LoadBalancer: albDimension,
            },
            statistic: "Sum",
            period: Duration.minutes(5),
            label: "Requests",
          }),
        ],
        width: 12,
        height: 6,
      }),
      new cloudwatch.GraphWidget({
        title: "ALB Target Response Time (seconds)",
        left: [
          new cloudwatch.Metric({
            namespace: "AWS/ApplicationELB",
            metricName: "TargetResponseTime",
            dimensionsMap: {
              LoadBalancer: albDimension,
            },
            statistic: "p50",
            period: Duration.minutes(5),
            label: "P50",
          }),
          new cloudwatch.Metric({
            namespace: "AWS/ApplicationELB",
            metricName: "TargetResponseTime",
            dimensionsMap: {
              LoadBalancer: albDimension,
            },
            statistic: "p95",
            period: Duration.minutes(5),
            label: "P95",
          }),
          new cloudwatch.Metric({
            namespace: "AWS/ApplicationELB",
            metricName: "TargetResponseTime",
            dimensionsMap: {
              LoadBalancer: albDimension,
            },
            statistic: "p99",
            period: Duration.minutes(5),
            label: "P99",
          }),
          new cloudwatch.Metric({
            namespace: "AWS/ApplicationELB",
            metricName: "TargetResponseTime",
            dimensionsMap: {
              LoadBalancer: albDimension,
            },
            statistic: "Average",
            period: Duration.minutes(5),
            label: "Average",
          }),
        ],
        width: 12,
        height: 6,
      })
    );

    dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: "ALB HTTP Error Codes",
        left: [
          new cloudwatch.Metric({
            namespace: "AWS/ApplicationELB",
            metricName: "HTTPCode_Target_4XX_Count",
            dimensionsMap: {
              LoadBalancer: albDimension,
            },
            statistic: "Sum",
            period: Duration.minutes(5),
            label: "4xx Errors",
          }),
          new cloudwatch.Metric({
            namespace: "AWS/ApplicationELB",
            metricName: "HTTPCode_Target_5XX_Count",
            dimensionsMap: {
              LoadBalancer: albDimension,
            },
            statistic: "Sum",
            period: Duration.minutes(5),
            label: "5xx Errors",
          }),
        ],
        width: 12,
        height: 6,
      }),
      new cloudwatch.GraphWidget({
        title: "ALB Target Health",
        left: [
          new cloudwatch.Metric({
            namespace: "AWS/ApplicationELB",
            metricName: "HealthyHostCount",
            dimensionsMap: {
              LoadBalancer: albDimension,
              TargetGroup: targetGroupDimension,
            },
            statistic: "Average",
            period: Duration.minutes(5),
            label: "Healthy Hosts",
          }),
          new cloudwatch.Metric({
            namespace: "AWS/ApplicationELB",
            metricName: "UnHealthyHostCount",
            dimensionsMap: {
              LoadBalancer: albDimension,
              TargetGroup: targetGroupDimension,
            },
            statistic: "Average",
            period: Duration.minutes(5),
            label: "Unhealthy Hosts",
          }),
        ],
        width: 12,
        height: 6,
      })
    );
  }
}

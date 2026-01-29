import {
  Stack,
  StackProps,
  RemovalPolicy,
  CfnOutput,
  Fn,
  Duration,
  Tags,
} from "aws-cdk-lib";
import * as iam from "aws-cdk-lib/aws-iam";
import * as logs from "aws-cdk-lib/aws-logs";
import * as sfn from "aws-cdk-lib/aws-stepfunctions";
import * as events from "aws-cdk-lib/aws-events";
import * as targets from "aws-cdk-lib/aws-events-targets";
import { Construct } from "constructs";
import { EnvConfig } from "../config/env-config";

export interface OrchestrationStackProps extends StackProps {
  config: EnvConfig;
}

export class OrchestrationStack extends Stack {
  public readonly stateMachine: sfn.StateMachine;
  public readonly scheduleRule: events.Rule;

  constructor(scope: Construct, id: string, props: OrchestrationStackProps) {
    super(scope, id, props);

    const { config } = props;

    // オーケストレーション設定がない場合はスキップ
    if (!config.orchestration) {
      throw new Error("Orchestration configuration is required");
    }

    // =========================================
    // 1. 他スタックからのインポート
    // =========================================

    // ECSクラスターARNのインポート
    const clusterArn = Fn.importValue(`${config.envName}-EcsClusterArn`);

    // タスク定義ARNのインポート
    const taskDefinitionArn = Fn.importValue(
      `${config.envName}-TaskDefinitionArn`
    );

    // タスクロールARN・タスク実行ロールARNのインポート
    const taskRoleArn = Fn.importValue(`${config.envName}-TaskRoleArn`);
    const executionRoleArn = Fn.importValue(
      `${config.envName}-TaskExecutionRoleArn`
    );

    // ECSセキュリティグループIDのインポート
    const ecsSecurityGroupId = Fn.importValue(
      `${config.envName}-EcsSecurityGroupId`
    );

    // SNSトピックARNのインポート（MonitoringStackから）
    const criticalAlertsTopicArn = Fn.importValue(
      `${config.envName}-CriticalAlertsTopicArn`
    );

    // =========================================
    // 2. CloudWatch Logsロググループ
    // =========================================
    const logGroup = new logs.LogGroup(this, "StateMachineLogGroup", {
      logGroupName: `/aws/stepfunctions/${config.envName}-sample-batch-workflow`,
      retention:
        config.logRetentionDays === 7
          ? logs.RetentionDays.ONE_WEEK
          : logs.RetentionDays.ONE_MONTH,
      removalPolicy:
        config.removalPolicy.logGroups === "DESTROY"
          ? RemovalPolicy.DESTROY
          : RemovalPolicy.RETAIN,
    });

    Tags.of(logGroup).add("Environment", config.envName);
    Tags.of(logGroup).add("Project", "project-template");
    Tags.of(logGroup).add("ManagedBy", "CDK");

    // =========================================
    // 3. Step Functions実行用IAMロール
    // =========================================
    const stateMachineRole = new iam.Role(this, "StateMachineRole", {
      roleName: `stepfunctions-role-${config.envName}`,
      assumedBy: new iam.ServicePrincipal("states.amazonaws.com"),
    });

    // ECS RunTask権限
    stateMachineRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["ecs:RunTask", "ecs:StopTask", "ecs:DescribeTasks"],
        resources: ["*"], // タスク定義はFn.importValueで動的に取得するため
      })
    );

    // EventsのPutTargets権限（ECS RunTask.sync用）
    stateMachineRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["events:PutTargets", "events:PutRule", "events:DescribeRule"],
        resources: [
          `arn:aws:events:${this.region}:${this.account}:rule/StepFunctionsGetEventsForECSTaskRule`,
        ],
      })
    );

    // PassRole権限（タスク実行ロール、タスクロール用）
    stateMachineRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["iam:PassRole"],
        resources: [taskRoleArn, executionRoleArn],
        conditions: {
          StringEquals: {
            "iam:PassedToService": "ecs-tasks.amazonaws.com",
          },
        },
      })
    );

    // SNS Publish権限
    stateMachineRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["sns:Publish"],
        resources: [criticalAlertsTopicArn],
      })
    );

    // CloudWatch Logs書き込み権限
    logGroup.grantWrite(stateMachineRole);

    // ロギング用の追加権限
    stateMachineRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          "logs:CreateLogDelivery",
          "logs:GetLogDelivery",
          "logs:UpdateLogDelivery",
          "logs:DeleteLogDelivery",
          "logs:ListLogDeliveries",
          "logs:PutResourcePolicy",
          "logs:DescribeResourcePolicies",
          "logs:DescribeLogGroups",
        ],
        resources: ["*"],
      })
    );

    Tags.of(stateMachineRole).add("Environment", config.envName);
    Tags.of(stateMachineRole).add("Project", "project-template");
    Tags.of(stateMachineRole).add("ManagedBy", "CDK");

    // =========================================
    // 4. Step Functionsステートマシン定義（ASL JSON形式）
    // =========================================

    // プライベートサブネットIDを取得
    const privateSubnetId1 = Fn.importValue(
      `${config.envName}-PrivateSubnetId1`
    );
    const privateSubnetId2 = Fn.importValue(
      `${config.envName}-PrivateSubnetId2`
    );

    // ASL定義をJSON形式で作成
    const stateMachineDefinition = {
      Comment: `Sample batch workflow for ${config.envName} environment`,
      StartAt: "RunBatchTask",
      States: {
        RunBatchTask: {
          Type: "Task",
          Resource: "arn:aws:states:::ecs:runTask.sync",
          Parameters: {
            Cluster: clusterArn,
            TaskDefinition: taskDefinitionArn,
            LaunchType: "FARGATE",
            NetworkConfiguration: {
              AwsvpcConfiguration: {
                Subnets: [privateSubnetId1, privateSubnetId2],
                SecurityGroups: [ecsSecurityGroupId],
                AssignPublicIp: "DISABLED",
              },
            },
            Overrides: {
              ContainerOverrides: [
                {
                  Name: "backend",
                  Command: ["python", config.orchestration.batchScriptPath],
                },
              ],
            },
          },
          ResultPath: "$.taskResult",
          Retry: [
            {
              ErrorEquals: ["States.TaskFailed", "ECS.AmazonECSException"],
              IntervalSeconds: 30,
              MaxAttempts: 3,
              BackoffRate: 2.0,
            },
          ],
          Catch: [
            {
              ErrorEquals: ["States.ALL"],
              ResultPath: "$.error",
              Next: "NotifyFailure",
            },
          ],
          Next: "ExecutionSucceeded",
        },
        NotifyFailure: {
          Type: "Task",
          Resource: "arn:aws:states:::sns:publish",
          Parameters: {
            TopicArn: criticalAlertsTopicArn,
            Subject: `[${config.envName.toUpperCase()}] Batch Execution Failed`,
            Message: {
              "message": "Batch execution failed",
              "error.$": "$.error.Error",
              "cause.$": "$.error.Cause",
              "executionName.$": "$$.Execution.Name",
              "stateMachineArn.$": "$$.StateMachine.Id",
              "timestamp.$": "$$.State.EnteredTime",
              "environment": config.envName,
            },
          },
          ResultPath: sfn.JsonPath.DISCARD,
          Next: "ExecutionFailed",
        },
        ExecutionFailed: {
          Type: "Fail",
          Error: "BatchExecutionError",
          Cause: "Batch execution failed after retries",
        },
        ExecutionSucceeded: {
          Type: "Succeed",
          Comment: "Batch execution completed successfully",
        },
      },
    };

    // ステートマシン作成
    this.stateMachine = new sfn.StateMachine(this, "SampleBatchWorkflow", {
      stateMachineName: `${config.envName}-sample-batch-workflow`,
      definitionBody: sfn.DefinitionBody.fromString(
        JSON.stringify(stateMachineDefinition)
      ),
      role: stateMachineRole,
      logs: {
        destination: logGroup,
        level: sfn.LogLevel.ALL,
        includeExecutionData: true,
      },
      tracingEnabled: true,
      timeout: Duration.hours(1),
    });

    Tags.of(this.stateMachine).add("Environment", config.envName);
    Tags.of(this.stateMachine).add("Project", "project-template");
    Tags.of(this.stateMachine).add("ManagedBy", "CDK");

    // =========================================
    // 5. EventBridgeルール
    // =========================================
    this.scheduleRule = new events.Rule(this, "ScheduleRule", {
      ruleName: `${config.envName}-sample-batch-schedule`,
      description: `Trigger sample batch workflow (${config.orchestration.scheduleExpression})`,
      schedule: events.Schedule.expression(
        config.orchestration.scheduleExpression
      ),
      enabled: config.orchestration.enabled,
    });

    // ステートマシンをターゲットとして追加
    this.scheduleRule.addTarget(
      new targets.SfnStateMachine(this.stateMachine, {
        input: events.RuleTargetInput.fromObject({
          triggerSource: "EventBridge",
          scheduledTime: events.EventField.time,
          environment: config.envName,
        }),
      })
    );

    Tags.of(this.scheduleRule).add("Environment", config.envName);
    Tags.of(this.scheduleRule).add("Project", "project-template");
    Tags.of(this.scheduleRule).add("ManagedBy", "CDK");

    // =========================================
    // 6. スタック出力
    // =========================================
    new CfnOutput(this, "StateMachineArn", {
      value: this.stateMachine.stateMachineArn,
      description: "Step Functions State Machine ARN",
      exportName: `${config.envName}-StateMachineArn`,
    });

    new CfnOutput(this, "StateMachineName", {
      value: this.stateMachine.stateMachineName,
      description: "Step Functions State Machine Name",
      exportName: `${config.envName}-StateMachineName`,
    });

    new CfnOutput(this, "ScheduleRuleName", {
      value: this.scheduleRule.ruleName,
      description: "EventBridge Schedule Rule Name",
      exportName: `${config.envName}-ScheduleRuleName`,
    });

    new CfnOutput(this, "ScheduleRuleEnabled", {
      value: config.orchestration.enabled ? "true" : "false",
      description: "EventBridge Schedule Rule Enabled Status",
    });

    new CfnOutput(this, "StateMachineLogGroupName", {
      value: logGroup.logGroupName,
      description: "Step Functions Log Group Name",
      exportName: `${config.envName}-StateMachineLogGroupName`,
    });
  }
}

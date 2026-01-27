import {
  Stack,
  StackProps,
  RemovalPolicy,
  CfnOutput,
  Fn,
  Duration,
  Tags,
} from "aws-cdk-lib";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as ecs from "aws-cdk-lib/aws-ecs";
import * as elbv2 from "aws-cdk-lib/aws-elasticloadbalancingv2";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as iam from "aws-cdk-lib/aws-iam";
import * as logs from "aws-cdk-lib/aws-logs";
import * as wafv2 from "aws-cdk-lib/aws-wafv2";
import * as secretsmanager from "aws-cdk-lib/aws-secretsmanager";
import { Construct } from "constructs";
import { EnvConfig } from "../config/env-config";

export interface ComputeStackProps extends StackProps {
  config: EnvConfig;
}

export class ComputeStack extends Stack {
  public readonly alb: elbv2.ApplicationLoadBalancer;
  public readonly ecsCluster: ecs.Cluster;
  public readonly ecsService: ecs.FargateService;

  constructor(scope: Construct, id: string, props: ComputeStackProps) {
    super(scope, id, props);

    const { config } = props;

    // =========================================
    // VPCのインポート（NetworkStackから）
    // =========================================
    const vpc = ec2.Vpc.fromVpcAttributes(this, "VPC", {
      vpcId: Fn.importValue(`${config.envName}-VpcId`),
      availabilityZones: config.availabilityZones,
      publicSubnetIds: [
        Fn.importValue(`${config.envName}-PublicSubnetId1`),
        Fn.importValue(`${config.envName}-PublicSubnetId2`),
      ],
      isolatedSubnetIds: [
        Fn.importValue(`${config.envName}-PrivateSubnetId1`),
        Fn.importValue(`${config.envName}-PrivateSubnetId2`),
      ],
    });

    // Secrets Managerからデータベース認証情報を参照
    const dbSecretArn = Fn.importValue(`${config.envName}-DbSecretArn`);
    const dbSecret = secretsmanager.Secret.fromSecretCompleteArn(
      this,
      "DbSecret",
      dbSecretArn
    );

    // データベースエンドポイントのインポート
    const dbClusterEndpoint = Fn.importValue(
      `${config.envName}-DbClusterEndpoint`
    );

    // WebAcl ARNのインポート（SecurityStackから）
    // const webAclArn = Fn.importValue(`${config.envName}-WebAclArn`);

    // =========================================
    // 1. ECRリポジトリのインポート（EcrStackから）
    // =========================================
    const ecrRepositoryUri = Fn.importValue(
      `${config.envName}-EcrRepositoryUri`,
    );
    const ecrRepositoryArn = Fn.importValue(
      `${config.envName}-EcrRepositoryArn`,
    );

    // =========================================
    // 2. ALBアクセスログ用S3バケット
    // =========================================
    const albLogBucket = new s3.Bucket(this, "AlbLogBucket", {
      bucketName: `alb-logs-${config.envName}-${this.account}`,
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      versioned: false,
      lifecycleRules: [
        {
          transitions: [
            {
              storageClass: s3.StorageClass.GLACIER,
              transitionAfter: Duration.days(90),
            },
          ],
          expiration: Duration.days(365),
        },
      ],
      removalPolicy:
        config.removalPolicy.s3Buckets === "DESTROY"
          ? RemovalPolicy.DESTROY
          : RemovalPolicy.RETAIN,
      autoDeleteObjects: config.removalPolicy.s3Buckets === "DESTROY",
    });

    Tags.of(albLogBucket).add("Environment", config.envName);
    Tags.of(albLogBucket).add("Project", "project-template");
    Tags.of(albLogBucket).add("ManagedBy", "CDK");

    // =========================================
    // 2.1 アプリケーション用S3バケット
    // =========================================
    const appBucket = new s3.Bucket(this, "AppBucket", {
      bucketName: `app-bucket-${config.envName}-${this.account}`,
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      versioned: true,
      removalPolicy:
        config.removalPolicy.s3Buckets === "DESTROY"
          ? RemovalPolicy.DESTROY
          : RemovalPolicy.RETAIN,
      autoDeleteObjects: config.removalPolicy.s3Buckets === "DESTROY",
    });

    Tags.of(appBucket).add("Environment", config.envName);
    Tags.of(appBucket).add("Project", "project-template");
    Tags.of(appBucket).add("ManagedBy", "CDK");

    // =========================================
    // 3. アプリケーションログ用S3バケット（Fluent Bit → S3）
    // =========================================
    // 注意: 現在はawslogsドライバーを使用しているため、このS3バケットは使用していません
    // 将来的にFluent Bitを有効化する際は、以下のコメントを解除してください
    /*
    const appLogBucket = new s3.Bucket(this, 'AppLogBucket', {
      bucketName: `app-logs-${config.envName}-${this.account}`,
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      versioned: true,
      lifecycleRules: [
        {
          transitions: [
            {
              storageClass: s3.StorageClass.GLACIER,
              transitionAfter: Duration.days(90)
            }
          ],
          expiration: Duration.days(365)
        }
      ],
      removalPolicy: config.removalPolicy.s3Buckets === 'DESTROY'
        ? RemovalPolicy.DESTROY
        : RemovalPolicy.RETAIN,
      autoDeleteObjects: config.removalPolicy.s3Buckets === 'DESTROY'
    });

    Tags.of(appLogBucket).add('Environment', config.envName);
    Tags.of(appLogBucket).add('Project', 'project-template');
    Tags.of(appLogBucket).add('ManagedBy', 'CDK');
    */

    // =========================================
    // 4. セキュリティグループ
    // =========================================

    // ALB用セキュリティグループ
    const albSecurityGroup = new ec2.SecurityGroup(this, "AlbSecurityGroup", {
      vpc,
      securityGroupName: `alb-sg-${config.envName}`,
      description: "Security group for Application Load Balancer",
      allowAllOutbound: true,
    });

    // HTTP (80) を許可
    albSecurityGroup.addIngressRule(
      ec2.Peer.anyIpv4(),
      ec2.Port.tcp(80),
      "Allow HTTP from anywhere",
    );

    // HTTPS (443) を許可（将来のHTTPS対応用）
    albSecurityGroup.addIngressRule(
      ec2.Peer.anyIpv4(),
      ec2.Port.tcp(443),
      "Allow HTTPS from anywhere",
    );

    Tags.of(albSecurityGroup).add("Environment", config.envName);
    Tags.of(albSecurityGroup).add("Project", "project-template");
    Tags.of(albSecurityGroup).add("ManagedBy", "CDK");

    // ECS用セキュリティグループ
    const ecsSecurityGroup = new ec2.SecurityGroup(this, "EcsSecurityGroup", {
      vpc,
      securityGroupName: `ecs-sg-${config.envName}`,
      description: "Security group for ECS Fargate tasks",
      allowAllOutbound: true,
    });

    // ALBからのアクセスを許可（ポート8000）
    ecsSecurityGroup.addIngressRule(
      albSecurityGroup,
      ec2.Port.tcp(8000),
      "Allow traffic from ALB",
    );

    Tags.of(ecsSecurityGroup).add("Environment", config.envName);
    Tags.of(ecsSecurityGroup).add("Project", "project-template");
    Tags.of(ecsSecurityGroup).add("ManagedBy", "CDK");

    // =========================================
    // 5. Application Load Balancer
    // =========================================
    this.alb = new elbv2.ApplicationLoadBalancer(this, "ALB", {
      vpc,
      loadBalancerName: `alb-${config.envName}`,
      internetFacing: true,
      vpcSubnets: { subnetType: ec2.SubnetType.PUBLIC },
      securityGroup: albSecurityGroup,
    });

    // ALBアクセスログの有効化
    this.alb.logAccessLogs(albLogBucket, `alb-${config.envName}`);

    Tags.of(this.alb).add("Environment", config.envName);
    Tags.of(this.alb).add("Project", "project-template");
    Tags.of(this.alb).add("ManagedBy", "CDK");

    // ターゲットグループ
    const targetGroup = new elbv2.ApplicationTargetGroup(this, "TargetGroup", {
      vpc,
      targetGroupName: `tg-${config.envName}`,
      port: 8000,
      protocol: elbv2.ApplicationProtocol.HTTP,
      targetType: elbv2.TargetType.IP,
      healthCheck: {
        path: "/api/v1/health",
        interval: Duration.seconds(30),
        timeout: Duration.seconds(5),
        healthyThresholdCount: 2,
        unhealthyThresholdCount: 3,
        healthyHttpCodes: "200",
      },
      deregistrationDelay: Duration.seconds(30),
    });

    // HTTPリスナー（ポート80）
    this.alb.addListener("HttpListener", {
      port: 80,
      protocol: elbv2.ApplicationProtocol.HTTP,
      defaultTargetGroups: [targetGroup],
    });

    // WAFの関連付け
    // new wafv2.CfnWebACLAssociation(this, 'WebACLAssociation', {
    //   resourceArn: this.alb.loadBalancerArn,
    //   webAclArn: webAclArn
    // });

    // =========================================
    // 6. ECS Cluster
    // =========================================
    this.ecsCluster = new ecs.Cluster(this, "EcsCluster", {
      vpc,
      clusterName: `cluster-${config.envName}`,
      containerInsightsV2: ecs.ContainerInsights.ENABLED,
    });

    Tags.of(this.ecsCluster).add("Environment", config.envName);
    Tags.of(this.ecsCluster).add("Project", "project-template");
    Tags.of(this.ecsCluster).add("ManagedBy", "CDK");

    // =========================================
    // 7. CloudWatch Logs ロググループ
    // =========================================
    const appLogGroup = new logs.LogGroup(this, "AppLogGroup", {
      logGroupName: `/ecs/${config.envName}/backend`,
      retention:
        config.logRetentionDays === 7
          ? logs.RetentionDays.ONE_WEEK
          : logs.RetentionDays.ONE_MONTH,
      removalPolicy:
        config.removalPolicy.logGroups === "DESTROY"
          ? RemovalPolicy.DESTROY
          : RemovalPolicy.RETAIN,
    });

    // =========================================
    // 8. IAMロール
    // =========================================

    // タスク実行ロール
    const executionRole = new iam.Role(this, "TaskExecutionRole", {
      roleName: `ecs-execution-role-${config.envName}`,
      assumedBy: new iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName(
          "service-role/AmazonECSTaskExecutionRolePolicy",
        ),
      ],
    });

    // ECRからのイメージプル権限（EcrStackのリポジトリ用）
    executionRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
        ],
        resources: ["*"],
      }),
    );

    // CloudWatch Logs書き込み権限
    appLogGroup.grantWrite(executionRole);

    // Secrets Manager読み取り権限
    executionRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["secretsmanager:GetSecretValue"],
        resources: [dbSecretArn],
      })
    );

    // タスクロール
    const taskRole = new iam.Role(this, "TaskRole", {
      roleName: `ecs-task-role-${config.envName}`,
      assumedBy: new iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
    });

    // S3ログバケットへの書き込み権限（Fluent Bit有効時に使用）
    // appLogBucket.grantWrite(taskRole);

    // アプリケーション用S3バケットへのアクセス権限
    appBucket.grantReadWrite(taskRole);

    // CloudWatch Logs書き込み権限
    appLogGroup.grantWrite(taskRole);

    // =========================================
    // 8.1 GitHub Actions用OIDC Provider & IAMロール
    // =========================================

    // GitHub設定がある場合のみOIDCプロバイダーとIAMロールを作成
    if (config.github) {
      // GitHub Actions OIDC Provider
      const githubProvider = new iam.OpenIdConnectProvider(
        this,
        "GithubOidcProvider",
        {
          url: "https://token.actions.githubusercontent.com",
          clientIds: ["sts.amazonaws.com"],
          thumbprints: ["6938fd4d98bab03faadb97b34396831e3780aea1"], // GitHub用のthumbprint
        },
      );

      // ブランチ条件の構築
      const branchConditions = config.github.branches.map(
        (branch) =>
          `repo:${config.github!.owner}/${config.github!.repository}:ref:refs/heads/${branch}`,
      );

      // GitHub Actions用IAMロール
      const githubActionsRole = new iam.Role(this, "GithubActionsRole", {
        roleName: `github-actions-role-${config.envName}`,
        assumedBy: new iam.FederatedPrincipal(
          githubProvider.openIdConnectProviderArn,
          {
            StringEquals: {
              "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
            },
            StringLike: {
              "token.actions.githubusercontent.com:sub": branchConditions,
            },
          },
          "sts:AssumeRoleWithWebIdentity",
        ),
      });

      // ECR GetAuthorizationToken権限（リソースは*である必要がある）
      githubActionsRole.addToPolicy(
        new iam.PolicyStatement({
          effect: iam.Effect.ALLOW,
          actions: ["ecr:GetAuthorizationToken"],
          resources: ["*"],
        }),
      );

      // ECR リポジトリ操作権限（EcrStackから参照）
      githubActionsRole.addToPolicy(
        new iam.PolicyStatement({
          effect: iam.Effect.ALLOW,
          actions: [
            "ecr:BatchCheckLayerAvailability",
            "ecr:GetDownloadUrlForLayer",
            "ecr:BatchGetImage",
            "ecr:PutImage",
            "ecr:InitiateLayerUpload",
            "ecr:UploadLayerPart",
            "ecr:CompleteLayerUpload",
          ],
          resources: [ecrRepositoryArn],
        }),
      );

      // ECS デプロイ権限
      githubActionsRole.addToPolicy(
        new iam.PolicyStatement({
          effect: iam.Effect.ALLOW,
          actions: [
            "ecs:RegisterTaskDefinition",
            "ecs:DescribeTaskDefinition",
            "ecs:DescribeServices",
            "ecs:UpdateService",
            "ecs:RunTask",
            "ecs:DescribeTasks",
          ],
          resources: ["*"], // タスク定義は事前にARNが分からないため
        }),
      );

      // PassRole権限（タスク実行ロール・タスクロール用）
      githubActionsRole.addToPolicy(
        new iam.PolicyStatement({
          effect: iam.Effect.ALLOW,
          actions: ["iam:PassRole"],
          resources: [executionRole.roleArn, taskRole.roleArn],
          conditions: {
            StringEquals: {
              "iam:PassedToService": "ecs-tasks.amazonaws.com",
            },
          },
        }),
      );

      Tags.of(githubActionsRole).add("Environment", config.envName);
      Tags.of(githubActionsRole).add("Project", "project-template");
      Tags.of(githubActionsRole).add("ManagedBy", "CDK");

      // CfnOutput
      new CfnOutput(this, "GithubActionsRoleArn", {
        value: githubActionsRole.roleArn,
        description: "GitHub Actions IAM Role ARN",
        exportName: `${config.envName}-GithubActionsRoleArn`,
      });

      new CfnOutput(this, "GithubOidcProviderArn", {
        value: githubProvider.openIdConnectProviderArn,
        description: "GitHub OIDC Provider ARN",
        exportName: `${config.envName}-GithubOidcProviderArn`,
      });
    }

    // =========================================
    // 9. ECS Task Definition
    // =========================================
    const taskDefinition = new ecs.FargateTaskDefinition(
      this,
      "TaskDefinition",
      {
        family: `backend-${config.envName}`,
        cpu: config.ecs.cpu,
        memoryLimitMiB: config.ecs.memory,
        executionRole: executionRole,
        taskRole: taskRole,
      },
    );

    // =========================================
    // Fluent Bit サイドカー（FireLens）- 現在は無効化
    // =========================================
    // 注意: PRIVATE_ISOLATEDサブネットからパブリックECRにアクセスできないため、
    // 現在はawslogsドライバーを使用しています。
    // Fluent Bitを有効化するには、以下のいずれかの対応が必要です：
    // 1. Fluent BitイメージをプライベートECRにコピー
    // 2. NATゲートウェイを追加（月額約$32のコスト増）
    // 3. 別のログ収集方法を検討
    /*
    const logRouter = taskDefinition.addFirelensLogRouter('log-router', {
      image: ecs.ContainerImage.fromRegistry('public.ecr.aws/aws-observability/aws-for-fluent-bit:stable'),
      firelensConfig: {
        type: ecs.FirelensLogRouterType.FLUENTBIT,
        options: {
          enableECSLogMetadata: true
        }
      },
      logging: ecs.LogDrivers.awsLogs({
        streamPrefix: 'firelens',
        logGroup: appLogGroup
      }),
      memoryReservationMiB: 50
    });

    logRouter.addPortMappings({
      containerPort: 24224,
      protocol: ecs.Protocol.TCP
    });
    */

    // メインコンテナ（FastAPI）
    taskDefinition.addContainer("app", {
      containerName: "backend",
      // クロススタック参照のためfromRegistryを使用
      image: ecs.ContainerImage.fromRegistry(`${ecrRepositoryUri}:latest`),
      essential: true,
      portMappings: [
        {
          containerPort: 8000,
          protocol: ecs.Protocol.TCP,
        },
      ],
      environment: {
        ENV: config.envName,
        LOG_LEVEL: config.envName === "prod" ? "INFO" : "DEBUG",
        // SMTP設定（Amazon SES SMTP Interface）
        SMTP_HOST: `email-smtp.${config.region}.amazonaws.com`,
        SMTP_PORT: "587",
        // S3設定（IAMロールで認証するためアクセスキーは不要）
        S3_BUCKET: appBucket.bucketName,
        S3_REGION: config.region,
        // データベースエンドポイント（URLはアプリ側でシークレットと組み合わせて構築）
        DATABASE_HOST: dbClusterEndpoint,
        DATABASE_PORT: "5432",
        DATABASE_NAME: "postgres",
      },
      secrets: {
        DATABASE_USER: ecs.Secret.fromSecretsManager(dbSecret, "username"),
        DATABASE_PASSWORD: ecs.Secret.fromSecretsManager(dbSecret, "password"),
      },

      // CloudWatch Logsへの直接出力（awslogsドライバー）
      logging: ecs.LogDrivers.awsLogs({
        streamPrefix: "backend",
        logGroup: appLogGroup,
      }),

      // Fluent Bit有効時のログ設定（現在は無効化）
      /*
      logging: ecs.LogDrivers.firelens({
        options: {
          Name: 'cloudwatch',
          region: config.region,
          log_group_name: appLogGroup.logGroupName,
          log_stream_prefix: 'app-',
          auto_create_group: 'false'
        }
      }),
      */
      healthCheck: {
        command: [
          "CMD-SHELL",
          "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')\" || exit 1",
        ],
        interval: Duration.seconds(30),
        timeout: Duration.seconds(5),
        retries: 3,
        startPeriod: Duration.seconds(60),
      },
    });

    // =========================================
    // 10. ECS Service
    // =========================================
    this.ecsService = new ecs.FargateService(this, "Service", {
      cluster: this.ecsCluster,
      serviceName: `backend-service-${config.envName}`,
      taskDefinition: taskDefinition,
      desiredCount: config.ecs.desiredCount,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
      securityGroups: [ecsSecurityGroup],
      assignPublicIp: false,
      enableExecuteCommand: true,
      circuitBreaker: {
        rollback: true,
      },
      deploymentController: {
        type: ecs.DeploymentControllerType.ECS,
      },
    });

    // ターゲットグループにサービスを登録（backendコンテナを明示的に指定）
    targetGroup.addTarget(
      this.ecsService.loadBalancerTarget({
        containerName: "backend",
        containerPort: 8000,
      }),
    );

    Tags.of(this.ecsService).add("Environment", config.envName);
    Tags.of(this.ecsService).add("Project", "project-template");
    Tags.of(this.ecsService).add("ManagedBy", "CDK");

    // =========================================
    // 11. Auto Scaling
    // =========================================
    const scalableTarget = this.ecsService.autoScaleTaskCount({
      minCapacity: config.ecs.minCapacity,
      maxCapacity: config.ecs.maxCapacity,
    });

    scalableTarget.scaleOnCpuUtilization("CpuScaling", {
      targetUtilizationPercent: 70,
      scaleInCooldown: Duration.seconds(60),
      scaleOutCooldown: Duration.seconds(60),
    });

    scalableTarget.scaleOnMemoryUtilization("MemoryScaling", {
      targetUtilizationPercent: 80,
      scaleInCooldown: Duration.seconds(60),
      scaleOutCooldown: Duration.seconds(60),
    });

    // =========================================
    // 12. スタック出力
    // =========================================
    // ECRリポジトリURIはEcrStackで出力済み

    new CfnOutput(this, "AlbDnsName", {
      value: this.alb.loadBalancerDnsName,
      description: "ALB DNS Name",
      exportName: `${config.envName}-AlbDnsName`,
    });

    new CfnOutput(this, "AlbArn", {
      value: this.alb.loadBalancerArn,
      description: "ALB ARN",
      exportName: `${config.envName}-AlbArn`,
    });

    new CfnOutput(this, "EcsClusterName", {
      value: this.ecsCluster.clusterName,
      description: "ECS Cluster Name",
      exportName: `${config.envName}-EcsClusterName`,
    });

    new CfnOutput(this, "EcsServiceName", {
      value: this.ecsService.serviceName,
      description: "ECS Service Name",
      exportName: `${config.envName}-EcsServiceName`,
    });

    new CfnOutput(this, "EcsSecurityGroupId", {
      value: ecsSecurityGroup.securityGroupId,
      description: "ECS Security Group ID",
      exportName: `${config.envName}-EcsSecurityGroupId`,
    });

    // AppLogBucketはFluent Bit有効時に使用
    /*
    new CfnOutput(this, 'AppLogBucketName', {
      value: appLogBucket.bucketName,
      description: 'Application Log Bucket Name',
      exportName: `${config.envName}-AppLogBucketName`
    });
    */

    new CfnOutput(this, "AppLogGroupName", {
      value: appLogGroup.logGroupName,
      description: "Application Log Group Name",
      exportName: `${config.envName}-AppLogGroupName`,
    });

    new CfnOutput(this, "AppBucketName", {
      value: appBucket.bucketName,
      description: "Application S3 Bucket Name",
      exportName: `${config.envName}-AppBucketName`,
    });
  }
}

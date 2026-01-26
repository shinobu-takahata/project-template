import {
  Stack,
  StackProps,
  RemovalPolicy,
  CfnOutput,
  Fn,
  Duration,
  Tags
} from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as wafv2 from 'aws-cdk-lib/aws-wafv2';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import { Construct } from 'constructs';
import { EnvConfig } from '../config/env-config';

export interface ComputeStackProps extends StackProps {
  config: EnvConfig;
}

export class ComputeStack extends Stack {
  public readonly ecrRepository: ecr.Repository;
  public readonly alb: elbv2.ApplicationLoadBalancer;
  public readonly ecsCluster: ecs.Cluster;
  public readonly ecsService: ecs.FargateService;

  constructor(scope: Construct, id: string, props: ComputeStackProps) {
    super(scope, id, props);

    const { config } = props;

    // =========================================
    // VPCのインポート（NetworkStackから）
    // =========================================
    const vpc = ec2.Vpc.fromVpcAttributes(this, 'VPC', {
      vpcId: Fn.importValue(`${config.envName}-VpcId`),
      availabilityZones: config.availabilityZones,
      publicSubnetIds: [
        Fn.importValue(`${config.envName}-PublicSubnetId1`),
        Fn.importValue(`${config.envName}-PublicSubnetId2`)
      ],
      isolatedSubnetIds: [
        Fn.importValue(`${config.envName}-PrivateSubnetId1`),
        Fn.importValue(`${config.envName}-PrivateSubnetId2`)
      ]
    });

    // Secrets Managerからデータベース認証情報を参照
    const dbSecretArn = Fn.importValue(`${config.envName}-DbSecretArn`);
    const dbSecret = secretsmanager.Secret.fromSecretCompleteArn(
      this,
      'DbSecret',
      dbSecretArn
    );

    // WebAcl ARNのインポート（SecurityStackから）
    const webAclArn = Fn.importValue(`${config.envName}-WebAclArn`);

    // =========================================
    // 1. ECRリポジトリ
    // =========================================
    this.ecrRepository = new ecr.Repository(this, 'BackendRepository', {
      repositoryName: `backend-${config.envName}`,
      imageScanOnPush: true,
      imageTagMutability: ecr.TagMutability.MUTABLE,
      lifecycleRules: [
        {
          maxImageCount: 10,
          description: 'Keep last 10 images'
        }
      ],
      encryption: ecr.RepositoryEncryption.AES_256,
      removalPolicy: config.removalPolicy.s3Buckets === 'DESTROY'
        ? RemovalPolicy.DESTROY
        : RemovalPolicy.RETAIN,
      emptyOnDelete: config.removalPolicy.s3Buckets === 'DESTROY'
    });

    Tags.of(this.ecrRepository).add('Environment', config.envName);
    Tags.of(this.ecrRepository).add('Project', 'project-template');
    Tags.of(this.ecrRepository).add('ManagedBy', 'CDK');

    // =========================================
    // 2. ALBアクセスログ用S3バケット
    // =========================================
    const albLogBucket = new s3.Bucket(this, 'AlbLogBucket', {
      bucketName: `alb-logs-${config.envName}-${this.account}`,
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      versioned: false,
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

    Tags.of(albLogBucket).add('Environment', config.envName);
    Tags.of(albLogBucket).add('Project', 'project-template');
    Tags.of(albLogBucket).add('ManagedBy', 'CDK');

    // =========================================
    // 3. アプリケーションログ用S3バケット（Fluent Bit → S3）
    // =========================================
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

    // =========================================
    // 4. セキュリティグループ
    // =========================================

    // ALB用セキュリティグループ
    const albSecurityGroup = new ec2.SecurityGroup(this, 'AlbSecurityGroup', {
      vpc,
      securityGroupName: `alb-sg-${config.envName}`,
      description: 'Security group for Application Load Balancer',
      allowAllOutbound: true
    });

    // HTTP (80) を許可
    albSecurityGroup.addIngressRule(
      ec2.Peer.anyIpv4(),
      ec2.Port.tcp(80),
      'Allow HTTP from anywhere'
    );

    // HTTPS (443) を許可（将来のHTTPS対応用）
    albSecurityGroup.addIngressRule(
      ec2.Peer.anyIpv4(),
      ec2.Port.tcp(443),
      'Allow HTTPS from anywhere'
    );

    Tags.of(albSecurityGroup).add('Environment', config.envName);
    Tags.of(albSecurityGroup).add('Project', 'project-template');
    Tags.of(albSecurityGroup).add('ManagedBy', 'CDK');

    // ECS用セキュリティグループ
    const ecsSecurityGroup = new ec2.SecurityGroup(this, 'EcsSecurityGroup', {
      vpc,
      securityGroupName: `ecs-sg-${config.envName}`,
      description: 'Security group for ECS Fargate tasks',
      allowAllOutbound: true
    });

    // ALBからのアクセスを許可（ポート8000）
    ecsSecurityGroup.addIngressRule(
      albSecurityGroup,
      ec2.Port.tcp(8000),
      'Allow traffic from ALB'
    );

    Tags.of(ecsSecurityGroup).add('Environment', config.envName);
    Tags.of(ecsSecurityGroup).add('Project', 'project-template');
    Tags.of(ecsSecurityGroup).add('ManagedBy', 'CDK');

    // =========================================
    // 5. Application Load Balancer
    // =========================================
    this.alb = new elbv2.ApplicationLoadBalancer(this, 'ALB', {
      vpc,
      loadBalancerName: `alb-${config.envName}`,
      internetFacing: true,
      vpcSubnets: { subnetType: ec2.SubnetType.PUBLIC },
      securityGroup: albSecurityGroup
    });

    // ALBアクセスログの有効化
    this.alb.logAccessLogs(albLogBucket, `alb-${config.envName}`);

    Tags.of(this.alb).add('Environment', config.envName);
    Tags.of(this.alb).add('Project', 'project-template');
    Tags.of(this.alb).add('ManagedBy', 'CDK');

    // ターゲットグループ
    const targetGroup = new elbv2.ApplicationTargetGroup(this, 'TargetGroup', {
      vpc,
      targetGroupName: `tg-${config.envName}`,
      port: 8000,
      protocol: elbv2.ApplicationProtocol.HTTP,
      targetType: elbv2.TargetType.IP,
      healthCheck: {
        path: '/health',
        interval: Duration.seconds(30),
        timeout: Duration.seconds(5),
        healthyThresholdCount: 2,
        unhealthyThresholdCount: 3,
        healthyHttpCodes: '200'
      },
      deregistrationDelay: Duration.seconds(30)
    });

    // HTTPリスナー（ポート80）
    this.alb.addListener('HttpListener', {
      port: 80,
      protocol: elbv2.ApplicationProtocol.HTTP,
      defaultTargetGroups: [targetGroup]
    });

    // WAFの関連付け
    new wafv2.CfnWebACLAssociation(this, 'WebACLAssociation', {
      resourceArn: this.alb.loadBalancerArn,
      webAclArn: webAclArn
    });

    // =========================================
    // 6. ECS Cluster
    // =========================================
    this.ecsCluster = new ecs.Cluster(this, 'EcsCluster', {
      vpc,
      clusterName: `cluster-${config.envName}`,
      containerInsightsV2: ecs.ContainerInsights.ENABLED
    });

    Tags.of(this.ecsCluster).add('Environment', config.envName);
    Tags.of(this.ecsCluster).add('Project', 'project-template');
    Tags.of(this.ecsCluster).add('ManagedBy', 'CDK');

    // =========================================
    // 7. CloudWatch Logs ロググループ
    // =========================================
    const appLogGroup = new logs.LogGroup(this, 'AppLogGroup', {
      logGroupName: `/ecs/${config.envName}/backend`,
      retention: config.logRetentionDays === 7
        ? logs.RetentionDays.ONE_WEEK
        : logs.RetentionDays.ONE_MONTH,
      removalPolicy: config.removalPolicy.logGroups === 'DESTROY'
        ? RemovalPolicy.DESTROY
        : RemovalPolicy.RETAIN
    });

    // =========================================
    // 8. IAMロール
    // =========================================

    // タスク実行ロール
    const executionRole = new iam.Role(this, 'TaskExecutionRole', {
      roleName: `ecs-execution-role-${config.envName}`,
      assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName(
          'service-role/AmazonECSTaskExecutionRolePolicy'
        )
      ]
    });

    // ECRからのイメージプル権限
    this.ecrRepository.grantPull(executionRole);

    // CloudWatch Logs書き込み権限
    appLogGroup.grantWrite(executionRole);

    // Secrets Manager読み取り権限
    executionRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          'secretsmanager:GetSecretValue'
        ],
        resources: [dbSecretArn]
      })
    );

    // タスクロール
    const taskRole = new iam.Role(this, 'TaskRole', {
      roleName: `ecs-task-role-${config.envName}`,
      assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com')
    });

    // S3ログバケットへの書き込み権限
    appLogBucket.grantWrite(taskRole);

    // CloudWatch Logs書き込み権限（Fluent Bit用）
    appLogGroup.grantWrite(taskRole);

    // =========================================
    // 9. ECS Task Definition
    // =========================================
    const taskDefinition = new ecs.FargateTaskDefinition(this, 'TaskDefinition', {
      family: `backend-${config.envName}`,
      cpu: config.ecs.cpu,
      memoryLimitMiB: config.ecs.memory,
      executionRole: executionRole,
      taskRole: taskRole
    });

    // Fluent Bit サイドカー（FireLens）
    const logRouter = taskDefinition.addFirelensLogRouter('log-router', {
      image: ecs.ContainerImage.fromRegistry('amazon/aws-for-fluent-bit:stable'),
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

    // Fluent Bit用のポートマッピングを追加（内部通信用）
    logRouter.addPortMappings({
      containerPort: 24224,
      protocol: ecs.Protocol.TCP
    });

    // メインコンテナ（FastAPI）
    taskDefinition.addContainer('app', {
      containerName: 'backend',
      image: ecs.ContainerImage.fromEcrRepository(this.ecrRepository, 'latest'),
      essential: true,
      portMappings: [
        {
          containerPort: 8000,
          protocol: ecs.Protocol.TCP
        }
      ],
      environment: {
        ENV: config.envName,
        LOG_LEVEL: config.envName === 'prod' ? 'INFO' : 'DEBUG',
        APP_LOG_BUCKET: appLogBucket.bucketName
      },
      secrets: {
        DATABASE_HOST: ecs.Secret.fromSecretsManager(dbSecret, 'host'),
        DATABASE_PORT: ecs.Secret.fromSecretsManager(dbSecret, 'port'),
        DATABASE_NAME: ecs.Secret.fromSecretsManager(dbSecret, 'dbname'),
        DATABASE_USER: ecs.Secret.fromSecretsManager(dbSecret, 'username'),
        DATABASE_PASSWORD: ecs.Secret.fromSecretsManager(dbSecret, 'password')
      },
      logging: ecs.LogDrivers.firelens({
        options: {
          Name: 'cloudwatch',
          region: config.region,
          log_group_name: appLogGroup.logGroupName,
          log_stream_prefix: 'app-',
          auto_create_group: 'false'
        }
      }),
      healthCheck: {
        command: ['CMD-SHELL', 'curl -f http://localhost:8000/health || exit 1'],
        interval: Duration.seconds(30),
        timeout: Duration.seconds(5),
        retries: 3,
        startPeriod: Duration.seconds(60)
      }
    });

    // =========================================
    // 10. ECS Service
    // =========================================
    this.ecsService = new ecs.FargateService(this, 'Service', {
      cluster: this.ecsCluster,
      serviceName: `backend-service-${config.envName}`,
      taskDefinition: taskDefinition,
      desiredCount: config.ecs.desiredCount,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
      securityGroups: [ecsSecurityGroup],
      assignPublicIp: false,
      enableExecuteCommand: true,
      circuitBreaker: {
        rollback: true
      },
      deploymentController: {
        type: ecs.DeploymentControllerType.ECS
      }
    });

    // ターゲットグループにサービスを登録
    this.ecsService.attachToApplicationTargetGroup(targetGroup);

    Tags.of(this.ecsService).add('Environment', config.envName);
    Tags.of(this.ecsService).add('Project', 'project-template');
    Tags.of(this.ecsService).add('ManagedBy', 'CDK');

    // =========================================
    // 11. Auto Scaling
    // =========================================
    const scalableTarget = this.ecsService.autoScaleTaskCount({
      minCapacity: config.ecs.minCapacity,
      maxCapacity: config.ecs.maxCapacity
    });

    scalableTarget.scaleOnCpuUtilization('CpuScaling', {
      targetUtilizationPercent: 70,
      scaleInCooldown: Duration.seconds(60),
      scaleOutCooldown: Duration.seconds(60)
    });

    scalableTarget.scaleOnMemoryUtilization('MemoryScaling', {
      targetUtilizationPercent: 80,
      scaleInCooldown: Duration.seconds(60),
      scaleOutCooldown: Duration.seconds(60)
    });

    // =========================================
    // 12. スタック出力
    // =========================================
    new CfnOutput(this, 'EcrRepositoryUri', {
      value: this.ecrRepository.repositoryUri,
      description: 'ECR Repository URI',
      exportName: `${config.envName}-EcrRepositoryUri`
    });

    new CfnOutput(this, 'AlbDnsName', {
      value: this.alb.loadBalancerDnsName,
      description: 'ALB DNS Name',
      exportName: `${config.envName}-AlbDnsName`
    });

    new CfnOutput(this, 'AlbArn', {
      value: this.alb.loadBalancerArn,
      description: 'ALB ARN',
      exportName: `${config.envName}-AlbArn`
    });

    new CfnOutput(this, 'EcsClusterName', {
      value: this.ecsCluster.clusterName,
      description: 'ECS Cluster Name',
      exportName: `${config.envName}-EcsClusterName`
    });

    new CfnOutput(this, 'EcsServiceName', {
      value: this.ecsService.serviceName,
      description: 'ECS Service Name',
      exportName: `${config.envName}-EcsServiceName`
    });

    new CfnOutput(this, 'EcsSecurityGroupId', {
      value: ecsSecurityGroup.securityGroupId,
      description: 'ECS Security Group ID',
      exportName: `${config.envName}-EcsSecurityGroupId`
    });

    new CfnOutput(this, 'AppLogBucketName', {
      value: appLogBucket.bucketName,
      description: 'Application Log Bucket Name',
      exportName: `${config.envName}-AppLogBucketName`
    });

    new CfnOutput(this, 'AppLogGroupName', {
      value: appLogGroup.logGroupName,
      description: 'Application Log Group Name',
      exportName: `${config.envName}-AppLogGroupName`
    });
  }
}

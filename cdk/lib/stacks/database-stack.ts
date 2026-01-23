import {
  Stack,
  StackProps,
  RemovalPolicy,
  CfnOutput,
  Fn,
  Duration,
  Tags
} from 'aws-cdk-lib';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as logs from 'aws-cdk-lib/aws-logs';
import { Construct } from 'constructs';
import { EnvConfig } from '../config/env-config';

export interface DatabaseStackProps extends StackProps {
  config: EnvConfig;
}

export class DatabaseStack extends Stack {
  constructor(scope: Construct, id: string, props: DatabaseStackProps) {
    super(scope, id, props);

    const { config } = props;

    // VPCのインポート（NetworkStackから）
    const vpc = ec2.Vpc.fromVpcAttributes(this, 'VPC', {
      vpcId: Fn.importValue(`${config.envName}-VpcId`),
      availabilityZones: config.availabilityZones,
      privateSubnetIds: [
        Fn.importValue(`${config.envName}-PrivateSubnetId1`),
        Fn.importValue(`${config.envName}-PrivateSubnetId2`)
      ]
    });

    // Secrets Manager: データベース認証情報
    const dbSecret = new secretsmanager.Secret(this, 'DBSecret', {
      secretName: `${config.envName}/aurora/credentials`,
      description: `Aurora database credentials for ${config.envName}`,
      generateSecretString: {
        secretStringTemplate: JSON.stringify({ username: 'dbadmin' }),
        generateStringKey: 'password',
        excludeCharacters: '"@/\\',
        passwordLength: 32,
        excludePunctuation: false
      },
      removalPolicy: config.removalPolicy.database === 'DESTROY'
        ? RemovalPolicy.DESTROY
        : RemovalPolicy.RETAIN
    });

    Tags.of(dbSecret).add('Environment', config.envName);
    Tags.of(dbSecret).add('Project', 'project-template');
    Tags.of(dbSecret).add('ManagedBy', 'CDK');

    // DBサブネットグループ
    const dbSubnetGroup = new rds.CfnDBSubnetGroup(this, 'DBSubnetGroup', {
      dbSubnetGroupName: `db-subnet-group-${config.envName}`,
      dbSubnetGroupDescription: `DB subnet group for ${config.envName}`,
      subnetIds: [
        Fn.importValue(`${config.envName}-PrivateSubnetId1`),
        Fn.importValue(`${config.envName}-PrivateSubnetId2`)
      ],
      tags: [
        { key: 'Environment', value: config.envName },
        { key: 'Project', value: 'project-template' },
        { key: 'ManagedBy', value: 'CDK' }
      ]
    });

    // DBセキュリティグループ
    const dbSecurityGroup = new ec2.SecurityGroup(this, 'DBSecurityGroup', {
      vpc,
      securityGroupName: `db-sg-${config.envName}`,
      description: 'Security group for Aurora database',
      allowAllOutbound: true
    });

    // PostgreSQLポート（5432）へのインバウンドルール
    // 注意: ECSセキュリティグループはフェーズ5で作成されるため、
    // ここでは送信元をVPC CIDR全体として設定
    dbSecurityGroup.addIngressRule(
      ec2.Peer.ipv4(config.vpcCidr),
      ec2.Port.tcp(5432),
      'Allow PostgreSQL access from VPC'
    );

    Tags.of(dbSecurityGroup).add('Environment', config.envName);
    Tags.of(dbSecurityGroup).add('Project', 'project-template');
    Tags.of(dbSecurityGroup).add('ManagedBy', 'CDK');

    // インスタンスタイプのパース（例: "db.t4g.small" -> InstanceClass.T4G, InstanceSize.SMALL）
    const instanceClassParts = config.aurora.instanceClass.split('.');
    const instanceFamily = instanceClassParts[1].toUpperCase(); // t4g -> T4G
    const instanceSize = instanceClassParts[2].toUpperCase();   // small -> SMALL

    // Aurora PostgreSQL Cluster
    const dbCluster = new rds.DatabaseCluster(this, 'AuroraCluster', {
      engine: rds.DatabaseClusterEngine.auroraPostgres({
        version: rds.AuroraPostgresEngineVersion.VER_15_14
      }),
      credentials: rds.Credentials.fromSecret(dbSecret),
      writer: rds.ClusterInstance.provisioned('WriterInstance', {
        instanceType: ec2.InstanceType.of(
          ec2.InstanceClass[instanceFamily as keyof typeof ec2.InstanceClass],
          ec2.InstanceSize[instanceSize as keyof typeof ec2.InstanceSize]
        ),
        availabilityZone: config.availabilityZones[0],
        enablePerformanceInsights: config.envName === 'prod',
        performanceInsightRetention: config.envName === 'prod'
          ? rds.PerformanceInsightRetention.DEFAULT
          : undefined
      }),
      readers: [
        rds.ClusterInstance.provisioned('ReaderInstance', {
          instanceType: ec2.InstanceType.of(
            ec2.InstanceClass[instanceFamily as keyof typeof ec2.InstanceClass],
            ec2.InstanceSize[instanceSize as keyof typeof ec2.InstanceSize]
          ),
          availabilityZone: config.availabilityZones[1],
          enablePerformanceInsights: config.envName === 'prod',
          performanceInsightRetention: config.envName === 'prod'
            ? rds.PerformanceInsightRetention.DEFAULT
            : undefined
        })
      ],
      vpc,
      vpcSubnets: {
        subnets: vpc.privateSubnets
      },
      securityGroups: [dbSecurityGroup],
      backup: {
        retention: Duration.days(config.aurora.backupRetentionDays),
        preferredWindow: '03:00-04:00'
      },
      preferredMaintenanceWindow: 'sun:19:00-sun:20:00',
      storageEncrypted: true,
      deletionProtection: config.aurora.deletionProtection,
      removalPolicy: config.removalPolicy.database === 'DESTROY'
        ? RemovalPolicy.DESTROY
        : config.removalPolicy.database === 'SNAPSHOT'
        ? RemovalPolicy.SNAPSHOT
        : RemovalPolicy.RETAIN,
      cloudwatchLogsExports: ['postgresql'],
      cloudwatchLogsRetention: config.logRetentionDays === 7
        ? logs.RetentionDays.ONE_WEEK
        : config.logRetentionDays === 30
        ? logs.RetentionDays.ONE_MONTH
        : logs.RetentionDays.ONE_WEEK
    });

    Tags.of(dbCluster).add('Environment', config.envName);
    Tags.of(dbCluster).add('Project', 'project-template');
    Tags.of(dbCluster).add('ManagedBy', 'CDK');

    // エクスポート: DBクラスタARN
    new CfnOutput(this, 'DbClusterArn', {
      value: dbCluster.clusterArn,
      description: 'Aurora cluster ARN',
      exportName: `${config.envName}-DbClusterArn`
    });

    // エクスポート: DBクラスタエンドポイント（書き込み用）
    new CfnOutput(this, 'DbClusterEndpoint', {
      value: dbCluster.clusterEndpoint.hostname,
      description: 'Aurora cluster writer endpoint',
      exportName: `${config.envName}-DbClusterEndpoint`
    });

    // エクスポート: DBクラスタ読み取りエンドポイント
    new CfnOutput(this, 'DbClusterReadEndpoint', {
      value: dbCluster.clusterReadEndpoint.hostname,
      description: 'Aurora cluster reader endpoint',
      exportName: `${config.envName}-DbClusterReadEndpoint`
    });

    // エクスポート: DBシークレットARN
    new CfnOutput(this, 'DbSecretArn', {
      value: dbSecret.secretArn,
      description: 'Database credentials secret ARN',
      exportName: `${config.envName}-DbSecretArn`
    });

    // エクスポート: DBセキュリティグループID
    new CfnOutput(this, 'DbSecurityGroupId', {
      value: dbSecurityGroup.securityGroupId,
      description: 'Database security group ID',
      exportName: `${config.envName}-DbSecurityGroupId`
    });
  }
}

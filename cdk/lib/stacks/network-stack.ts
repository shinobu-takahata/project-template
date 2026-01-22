import { Stack, StackProps, RemovalPolicy, CfnOutput, Tags } from 'aws-cdk-lib';
import { Vpc, SubnetType, IpAddresses, SecurityGroup, Peer, Port, GatewayVpcEndpointAwsService, InterfaceVpcEndpointAwsService, FlowLogDestination, FlowLogTrafficType } from 'aws-cdk-lib/aws-ec2';
import { LogGroup, RetentionDays } from 'aws-cdk-lib/aws-logs';
import { IHostedZone } from 'aws-cdk-lib/aws-route53';
import { Construct } from 'constructs';
import { EnvConfig } from '../config/env-config';

export interface NetworkStackProps extends StackProps {
  config: EnvConfig;
}

export class NetworkStack extends Stack {
  public readonly vpc: Vpc;
  public readonly hostedZone: IHostedZone;

  constructor(scope: Construct, id: string, props: NetworkStackProps) {
    super(scope, id, props);

    const { config } = props;

    // VPCフローログ用のロググループ
    const flowLogGroup = new LogGroup(this, 'VpcFlowLogGroup', {
      logGroupName: `/aws/vpc/flowlogs/${config.envName}`,
      retention: config.logRetentionDays === 7 
        ? RetentionDays.ONE_WEEK 
        : RetentionDays.ONE_MONTH,
      removalPolicy: config.removalPolicy.logGroups === 'DESTROY'
        ? RemovalPolicy.DESTROY
        : RemovalPolicy.RETAIN,
    });

    // VPC作成
    this.vpc = new Vpc(this, 'Vpc', {
      ipAddresses: IpAddresses.cidr(config.vpcCidr),
      availabilityZones: config.availabilityZones,
      natGateways: 0, // NAT Gatewayは使用しない（コスト最適化）
      subnetConfiguration: [
        {
          name: 'Public',
          subnetType: SubnetType.PUBLIC,
          cidrMask: 24,
        },
        {
          name: 'Private',
          subnetType: SubnetType.PRIVATE_ISOLATED, // インターネット接続なし
          cidrMask: 24,
        },
      ],
      flowLogs: {
        cloudwatch: {
          destination: FlowLogDestination.toCloudWatchLogs(flowLogGroup),
          trafficType: FlowLogTrafficType.ALL,
        },
      },
    });

    // タグ付け
    Tags.of(this.vpc).add('Environment', config.envName);
    Tags.of(this.vpc).add('Project', 'project-template');
    Tags.of(this.vpc).add('ManagedBy', 'CDK');

    // VPCエンドポイントの作成（useVpcEndpointsがtrueの場合）
    if (config.useVpcEndpoints) {
      this.createVpcEndpoints();
    }

    // Route 53 Hosted Zoneの参照
    // 注意: fromLookupは実際のAWS環境にアクセスするため、
    // ドメインが存在しない場合はコメントアウトしてください
    // TODO: Hosted Zoneを作成してから、この部分を有効化する
    /*
    try {
      this.hostedZone = HostedZone.fromLookup(this, 'HostedZone', {
        domainName: config.domainName.replace(/^(dev-|prod-)?api\./, ''), // example.com部分を取得
      });
    } catch (error) {
      // Hosted Zoneが存在しない場合は、新規作成（コメントアウト推奨）
      // 本番環境では事前にHosted Zoneを作成することを推奨
      console.warn(`Hosted Zone not found for ${config.domainName}, skipping...`);
      // this.hostedZone = new HostedZone(this, 'HostedZone', {
      //   zoneName: config.domainName.replace(/^(dev-|prod-)?api\./, ''),
      // });
    }
    */

    // スタック出力
    new CfnOutput(this, 'VpcId', {
      value: this.vpc.vpcId,
      description: 'VPC ID',
      exportName: `${config.envName}-VpcId`,
    });

    new CfnOutput(this, 'VpcCidr', {
      value: this.vpc.vpcCidrBlock,
      description: 'VPC CIDR Block',
    });
  }

  private createVpcEndpoints() {
    // Gateway型エンドポイント（S3）- 無料
    this.vpc.addGatewayEndpoint('S3Endpoint', {
      service: GatewayVpcEndpointAwsService.S3,
      subnets: [{ subnetType: SubnetType.PRIVATE_ISOLATED }],
    });

    // Interface型エンドポイント用のセキュリティグループ
    const vpcEndpointSg = new SecurityGroup(this, 'VpcEndpointSg', {
      vpc: this.vpc,
      description: 'Security group for VPC endpoints',
      allowAllOutbound: true,
    });

    // VPC CIDR範囲からのHTTPSアクセスを許可
    vpcEndpointSg.addIngressRule(
      Peer.ipv4(this.vpc.vpcCidrBlock),
      Port.tcp(443),
      'Allow HTTPS from VPC'
    );

    // ECR API エンドポイント
    this.vpc.addInterfaceEndpoint('EcrApiEndpoint', {
      service: InterfaceVpcEndpointAwsService.ECR,
      subnets: { subnetType: SubnetType.PRIVATE_ISOLATED },
      securityGroups: [vpcEndpointSg],
      privateDnsEnabled: true,
    });

    // ECR DKR エンドポイント
    this.vpc.addInterfaceEndpoint('EcrDkrEndpoint', {
      service: InterfaceVpcEndpointAwsService.ECR_DOCKER,
      subnets: { subnetType: SubnetType.PRIVATE_ISOLATED },
      securityGroups: [vpcEndpointSg],
      privateDnsEnabled: true,
    });

    // Secrets Manager エンドポイント
    this.vpc.addInterfaceEndpoint('SecretsManagerEndpoint', {
      service: InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
      subnets: { subnetType: SubnetType.PRIVATE_ISOLATED },
      securityGroups: [vpcEndpointSg],
      privateDnsEnabled: true,
    });

    // CloudWatch Logs エンドポイント
    this.vpc.addInterfaceEndpoint('CloudWatchLogsEndpoint', {
      service: InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS,
      subnets: { subnetType: SubnetType.PRIVATE_ISOLATED },
      securityGroups: [vpcEndpointSg],
      privateDnsEnabled: true,
    });
  }
}

import { Stack, StackProps, RemovalPolicy, CfnOutput } from "aws-cdk-lib";
import { CfnDetector } from "aws-cdk-lib/aws-guardduty";
import {
  CfnConfigurationRecorder,
  CfnDeliveryChannel,
} from "aws-cdk-lib/aws-config";
import { CfnWebACL } from "aws-cdk-lib/aws-wafv2";
import {
  Bucket,
  BucketEncryption,
  BlockPublicAccess,
} from "aws-cdk-lib/aws-s3";
import {
  Role,
  ServicePrincipal,
  ManagedPolicy,
  PolicyStatement,
  Effect,
} from "aws-cdk-lib/aws-iam";
import { Construct } from "constructs";
import { EnvConfig } from "../config/env-config";

export interface SecurityStackProps extends StackProps {
  config: EnvConfig;
}

export class SecurityStack extends Stack {
  public readonly webAclArn: string;

  constructor(scope: Construct, id: string, props: SecurityStackProps) {
    super(scope, id, props);

    const { config } = props;

    // =========================================
    // 1. GuardDuty Detector
    // =========================================
    const guardDutyDetector = new CfnDetector(this, "GuardDutyDetector", {
      enable: true,
    });

    // =========================================
    // 2. AWS Config - S3 Bucket
    // =========================================
    const configBucket = new Bucket(this, "ConfigBucket", {
      bucketName: `config-${config.envName}-${this.account}`,
      encryption: BucketEncryption.S3_MANAGED,
      versioned: true,
      blockPublicAccess: BlockPublicAccess.BLOCK_ALL,
      removalPolicy:
        config.removalPolicy.s3Buckets === "DESTROY"
          ? RemovalPolicy.DESTROY
          : RemovalPolicy.RETAIN,
      autoDeleteObjects: config.removalPolicy.s3Buckets === "DESTROY",
    });

    // S3バケットポリシー - AWS Configサービスからのアクセスを許可
    configBucket.addToResourcePolicy(
      new PolicyStatement({
        sid: "AWSConfigBucketPermissionsCheck",
        effect: Effect.ALLOW,
        principals: [new ServicePrincipal("config.amazonaws.com")],
        actions: ["s3:GetBucketAcl"],
        resources: [configBucket.bucketArn],
      }),
    );

    configBucket.addToResourcePolicy(
      new PolicyStatement({
        sid: "AWSConfigBucketExistenceCheck",
        effect: Effect.ALLOW,
        principals: [new ServicePrincipal("config.amazonaws.com")],
        actions: ["s3:ListBucket"],
        resources: [configBucket.bucketArn],
      }),
    );

    configBucket.addToResourcePolicy(
      new PolicyStatement({
        sid: "AWSConfigBucketPutObject",
        effect: Effect.ALLOW,
        principals: [new ServicePrincipal("config.amazonaws.com")],
        actions: ["s3:PutObject"],
        resources: [`${configBucket.bucketArn}/*`],
        conditions: {
          StringEquals: {
            "s3:x-amz-acl": "bucket-owner-full-control",
          },
        },
      }),
    );

    // =========================================
    // 3. AWS Config - IAM Role
    // =========================================
    const configRole = new Role(this, "ConfigRole", {
      assumedBy: new ServicePrincipal("config.amazonaws.com"),
      managedPolicies: [
        ManagedPolicy.fromAwsManagedPolicyName("service-role/AWS_ConfigRole"),
      ],
    });

    // S3バケットへの書き込み権限を付与
    configBucket.grantWrite(configRole);

    // =========================================
    // 4. AWS Config - Configuration Recorder
    // =========================================
    const configRecorder = new CfnConfigurationRecorder(
      this,
      "ConfigRecorder",
      {
        name: `config-recorder-${config.envName}`,
        roleArn: configRole.roleArn,
        recordingGroup: {
          allSupported: true,
          includeGlobalResourceTypes: true,
        },
      },
    );

    // =========================================
    // 5. AWS Config - Delivery Channel
    // =========================================
    const deliveryChannel = new CfnDeliveryChannel(this, "DeliveryChannel", {
      name: `config-delivery-${config.envName}`,
      s3BucketName: configBucket.bucketName,
      configSnapshotDeliveryProperties: {
        deliveryFrequency: "TwentyFour_Hours",
      },
    });

    // ConfigRecorderはDelivery Channelに依存
    // configRecorder.addDependency(deliveryChannel);

    // =========================================
    // 6. WAF Web ACL
    // =========================================
    const webAcl = new CfnWebACL(this, "WebACL", {
      scope: "REGIONAL",
      defaultAction: { allow: {} },
      visibilityConfig: {
        sampledRequestsEnabled: true,
        cloudWatchMetricsEnabled: true,
        metricName: `WebACL-${config.envName}`,
      },
      rules: [
        // ルール1: AWSManagedRulesCommonRuleSet
        {
          name: "AWSManagedRulesCommonRuleSet",
          priority: 1,
          statement: {
            managedRuleGroupStatement: {
              vendorName: "AWS",
              name: "AWSManagedRulesCommonRuleSet",
            },
          },
          overrideAction: { none: {} },
          visibilityConfig: {
            sampledRequestsEnabled: true,
            cloudWatchMetricsEnabled: true,
            metricName: "AWSManagedRulesCommonRuleSetMetric",
          },
        },
        // ルール2: AWSManagedRulesKnownBadInputsRuleSet
        {
          name: "AWSManagedRulesKnownBadInputsRuleSet",
          priority: 2,
          statement: {
            managedRuleGroupStatement: {
              vendorName: "AWS",
              name: "AWSManagedRulesKnownBadInputsRuleSet",
            },
          },
          overrideAction: { none: {} },
          visibilityConfig: {
            sampledRequestsEnabled: true,
            cloudWatchMetricsEnabled: true,
            metricName: "AWSManagedRulesKnownBadInputsRuleSetMetric",
          },
        },
        // ルール3: AWSManagedRulesSQLiRuleSet
        {
          name: "AWSManagedRulesSQLiRuleSet",
          priority: 3,
          statement: {
            managedRuleGroupStatement: {
              vendorName: "AWS",
              name: "AWSManagedRulesSQLiRuleSet",
            },
          },
          overrideAction: { none: {} },
          visibilityConfig: {
            sampledRequestsEnabled: true,
            cloudWatchMetricsEnabled: true,
            metricName: "AWSManagedRulesSQLiRuleSetMetric",
          },
        },
      ],
    });

    this.webAclArn = webAcl.attrArn;

    // =========================================
    // 7. スタック出力
    // =========================================
    new CfnOutput(this, "WebAclArn", {
      value: webAcl.attrArn,
      description: "WAF Web ACL ARN",
      exportName: `${config.envName}-WebAclArn`,
    });

    new CfnOutput(this, "ConfigBucketName", {
      value: configBucket.bucketName,
      description: "AWS Config S3 Bucket Name",
    });

    new CfnOutput(this, "GuardDutyDetectorId", {
      value: guardDutyDetector.ref,
      description: "GuardDuty Detector ID",
    });
  }
}

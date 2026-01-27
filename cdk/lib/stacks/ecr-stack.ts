import * as cdk from 'aws-cdk-lib';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import { Construct } from 'constructs';
import { EnvConfig } from '../config/env-config';

export interface EcrStackProps extends cdk.StackProps {
  config: EnvConfig;
}

export class EcrStack extends cdk.Stack {
  public readonly repository: ecr.Repository;

  constructor(scope: Construct, id: string, props: EcrStackProps) {
    super(scope, id, props);

    const { config } = props;

    // Backend ECR Repository
    this.repository = new ecr.Repository(this, 'BackendRepository', {
      repositoryName: `backend-${config.envName}`,

      // イメージスキャン設定（脆弱性検出）
      imageScanOnPush: true,

      // タグの変更可否（CI/CDで上書き可能にするためMUTABLE）
      imageTagMutability: ecr.TagMutability.MUTABLE,

      // ライフサイクルポリシー（最新10イメージのみ保持）
      lifecycleRules: [
        {
          rulePriority: 1,
          description: 'Keep last 10 images',
          maxImageCount: 10,
        },
      ],

      // 暗号化設定（AES256）
      encryption: ecr.RepositoryEncryption.AES_256,

      // 削除ポリシー（環境別設定）
      removalPolicy:
        config.removalPolicy.ecrRepositories === 'DESTROY'
          ? cdk.RemovalPolicy.DESTROY
          : cdk.RemovalPolicy.RETAIN,

      // スタック削除時にイメージを削除（開発環境のみ）
      emptyOnDelete: config.removalPolicy.ecrRepositories === 'DESTROY',
    });

    // CloudFormation Outputs（スタック間連携用）
    new cdk.CfnOutput(this, 'EcrRepositoryUri', {
      value: this.repository.repositoryUri,
      description: 'ECR Repository URI',
      exportName: `${config.envName}-EcrRepositoryUri`,
    });

    new cdk.CfnOutput(this, 'EcrRepositoryArn', {
      value: this.repository.repositoryArn,
      description: 'ECR Repository ARN',
      exportName: `${config.envName}-EcrRepositoryArn`,
    });

    new cdk.CfnOutput(this, 'EcrRepositoryName', {
      value: this.repository.repositoryName,
      description: 'ECR Repository Name',
      exportName: `${config.envName}-EcrRepositoryName`,
    });
  }
}

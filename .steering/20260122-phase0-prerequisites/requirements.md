# フェーズ0: 事前準備 - 要求事項

## 概要
AWS CDK実装を開始する前に、必要な開発環境とツール、GitHub連携などをセットアップし、動作確認を行います。

## 目的
- AWS CDK開発に必要なツールのインストール確認
- AWSアカウントとプロファイルの設定確認
- AWS環境のBootstrap実施
- GitHub連携の準備

## スコープ

### 実施すること
1. **開発環境の確認**
   - Node.js 18以上がインストールされているか確認
   - AWS CLI v2がインストールされているか確認
   - AWS CDK CLIがインストールされているか確認

2. **AWS設定の確認**
   - AWSアカウントへのアクセス権限確認
   - プロファイル設定の確認
   - リージョン設定の確認（ap-northeast-1）

3. **AWS環境のBootstrap**
   - ap-northeast-1リージョンでのCDK Bootstrap実施
   - Bootstrap完了の確認

4. **GitHub連携の準備**
   - GitHub Personal Access Tokenの発行（CI/CD用）
   - リポジトリの準備確認

### 実施しないこと
- CDKコードの実装
- AWSリソースの作成（Bootstrap用のリソースを除く）
- 実際のアプリケーションのデプロイ
- ドメインの取得・設定（後のフェーズで実施）
- ACM証明書の作成（フェーズ5で実施）

## 受け入れ条件

### 必須条件
1. Node.js 18以上がインストールされている
2. AWS CLI v2がインストールされている
3. AWS CDK CLI v2がインストールされている
4. AWSプロファイルが設定されている
5. ap-northeast-1リージョンがBootstrapされている
6. GitHub Personal Access Tokenが発行されている（CI/CD用）

### 確認項目
- [ ] `node --version` で v18以上が表示される
- [ ] `aws --version` でAWS CLI v2が表示される
- [ ] `cdk --version` でCDK v2が表示される
- [ ] `aws configure list` でプロファイルが設定されている
- [ ] `aws sts get-caller-identity` でアカウント情報が取得できる
- [ ] `cdk bootstrap aws://ACCOUNT-ID/ap-northeast-1` が成功する
- [ ] GitHub Personal Access Tokenが発行されている

## 技術要件

### 必要なツール
- **Node.js**: v18.0.0以上（推奨: LTS版）
- **npm**: v8.0.0以上（Node.jsに付属）
- **AWS CLI**: v2.x
- **AWS CDK CLI**: v2.x（グローバルインストール）

### 必要なAWS権限
CDKを実行するために、以下のサービスへのアクセス権限が必要です：
- CloudFormation（スタック作成・更新・削除）
- IAM（ロール・ポリシー作成）
- S3（CDK資産バケット）
- ECR（コンテナイメージリポジトリ）
- VPC、ECS、RDS、Route 53など各種AWSサービス

### Bootstrap要件
CDKを使用するには、対象リージョンでBootstrapが必要です。
Bootstrapにより以下のリソースが作成されます：
- S3バケット（CDK資産保存用）: `cdk-*-assets-{ACCOUNT-ID}-ap-northeast-1`
- ECRリポジトリ（コンテナイメージ用）: `cdk-*-container-assets-{ACCOUNT-ID}-ap-northeast-1`
- IAMロール（CloudFormation実行用）

**Bootstrapコマンド**:
```bash
cdk bootstrap aws://ACCOUNT-ID/ap-northeast-1
```

### GitHub要件
- GitHub Personal Access Token
  - スコープ: `repo`（リポジトリへのフルアクセス）
  - 用途: CI/CDパイプライン構築時に使用
  - 有効期限: 90日以上推奨
  - 保管: 安全な場所に保管（後のフェーズで使用）

## 制約事項
- AWSアカウントが必要
- 適切なIAM権限が付与されている必要がある
- インターネット接続が必要（npmパッケージのダウンロード、AWS APIアクセス用）
- GitHubアカウントが必要

## 参照ドキュメント
- [docs/architecture/implements_aws_by_cdk_plan.md](../../docs/architecture/implements_aws_by_cdk_plan.md) - 事前準備セクション（行1045-1056）

## 成果物
1. 開発環境の確認結果レポート
2. AWS設定の確認結果
3. Bootstrap完了の確認
4. GitHub Personal Access Token（安全に保管）

# フェーズ0: 事前準備 - 設計

## 概要
事前準備フェーズでは、CDK実装に必要な環境を整備します。CDK開発コンテナ内で実行することを前提とし、AWS環境の準備とGitHub連携の設定を行います。

## 変更内容

### 実施する作業
このフェーズでは、以下の確認と設定を行います：

#### 1. CDK開発コンテナ環境の確認
- コンテナ内のNode.js、npm、AWS CLI、AWS CDK CLIのバージョン確認
- コンテナが正しく起動していることの確認

#### 2. AWS認証情報の確認
- コンテナからAWS CLIが使えることを確認
- 認証情報の有効性確認
- 必要な権限の確認

#### 3. AWS CDK Bootstrap
- ap-northeast-1リージョンでCDK Bootstrapを実行
- Bootstrap完了後のリソース確認

#### 4. GitHub連携準備
- Personal Access Tokenの発行手順確認
- トークンの安全な保管方法の確認

## 実装アプローチ

### 1. CDK開発コンテナの起動と確認
コンテナ環境がセットアップされていることを前提とします。

```bash
# コンテナ内でツールバージョン確認
node --version
npm --version
aws --version
cdk --version
```

**期待される出力**:
- Node.js: v18.x.x 以上
- npm: v8.x.x 以上
- AWS CLI: aws-cli/2.x.x
- CDK CLI: 2.x.x

**注意**: これらのツールは既にコンテナイメージに含まれているはずです。

### 2. AWS認証情報確認方法
コンテナ内から以下のコマンドでAWS認証を確認します：

```bash
# 利用可能なプロファイルを確認
cat ~/.aws/config

# AWS_PROFILEを設定（使用するプロファイル名に置き換える）
export AWS_PROFILE=your-profile-name

# リージョンを設定
export AWS_REGION=ap-northeast-1

# アカウント情報取得
aws sts get-caller-identity
```

**認証情報の提供方法**:
- ホストマシンの `~/.aws` ディレクトリをコンテナにマウント（docker-compose.yml で設定済み）
- **重要**: `AWS_PROFILE` 環境変数を明示的に設定する必要があります
  - `default` プロファイルが存在しない場合、プロファイル名の指定が必須
  - 推奨: コンテナ起動時に `-e AWS_PROFILE=your-profile-name` を指定
  - または、コンテナ内で `export AWS_PROFILE=your-profile-name` を実行

**期待される出力**:
- アカウントIDとARNが取得できる
  ```json
  {
      "UserId": "AIDA...",
      "Account": "123456789012",
      "Arn": "arn:aws:iam::123456789012:user/your-user"
  }
  ```

### 3. AWS CDK Bootstrap実行
コンテナ内から以下のコマンドを実行します：

```bash
# アカウントIDを取得
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Bootstrap実行
cdk bootstrap aws://${AWS_ACCOUNT_ID}/ap-northeast-1
```

**Bootstrap完了の確認**:
```bash
# CloudFormationスタックの確認
aws cloudformation describe-stacks \
  --stack-name CDKToolkit \
  --region ap-northeast-1 \
  --query 'Stacks[0].StackStatus' \
  --output text
# 期待される出力: CREATE_COMPLETE または UPDATE_COMPLETE

# S3バケットの確認
aws s3 ls | grep cdk

# ECRリポジトリの確認
aws ecr describe-repositories \
  --region ap-northeast-1 \
  --query 'repositories[?contains(repositoryName, `cdk`)].repositoryName'
```

**作成されるリソース**:
- CloudFormation Stack: `CDKToolkit`
- S3 Bucket: `cdk-*-assets-{ACCOUNT-ID}-ap-northeast-1`
- ECR Repository: `cdk-*-container-assets-{ACCOUNT-ID}-ap-northeast-1`
- IAM Role: CloudFormation実行用ロール

### 4. GitHub Personal Access Token発行
以下の手順でトークンを発行します：

1. GitHubにログイン
2. Settings → Developer settings → Personal access tokens → Tokens (classic) に移動
3. "Generate new token (classic)" をクリック
4. トークンの設定:
   - Note: `CDK CI/CD Pipeline`
   - Expiration: 90日以上
   - Scopes: `repo` にチェック
5. "Generate token" をクリック
6. 表示されたトークンを安全な場所にコピー（再表示不可）

**保管方法**:
- パスワードマネージャーに保存
- または環境変数として設定（コンテナ起動時に渡す）
```bash
export GITHUB_TOKEN=your_token_here
```
- または `.env` ファイルに保存（`.gitignore` に追加済みであることを確認）

## 変更するコンポーネント
このフェーズではコードの変更はありません。環境の確認と準備のみを行います。

## データ構造の変更
なし

## 影響範囲の分析

### 影響するシステム
- CDK開発コンテナ環境
- AWS環境（Bootstrapリソースの作成）
  - CloudFormation Stack: `CDKToolkit`
  - S3 Bucket: `cdk-*-assets-{ACCOUNT-ID}-ap-northeast-1`
  - ECR Repository: `cdk-*-container-assets-{ACCOUNT-ID}-ap-northeast-1`
  - IAM Role: CloudFormation実行用ロール

### コンテナ環境の前提条件
- DevContainerまたはDockerコンテナが起動済み
- AWS認証情報がコンテナ内で利用可能
- インターネット接続が可能

### リスクと対策
1. **リスク**: コンテナからAWS認証情報にアクセスできない
   - **対策**: `~/.aws` ディレクトリのマウント確認、または環境変数の設定確認

2. **リスク**: Bootstrap実行に必要な権限が不足している
   - **対策**: 事前にIAM権限を確認、必要に応じて管理者に権限付与を依頼

3. **リスク**: すでにBootstrapされている環境で再実行
   - **対策**: Bootstrapは冪等性があり、既存環境の再実行も安全

4. **リスク**: GitHub Personal Access Tokenの漏洩
   - **対策**: トークンはパスワードマネージャーで管理、公開リポジトリにコミットしない

## トラブルシューティング

### コンテナ内でAWS CLIが認証エラーになる場合
```bash
# ホストの認証情報がマウントされているか確認
ls -la ~/.aws

# 環境変数の確認
env | grep AWS
```

**対策**:
- DevContainerの設定ファイル（`.devcontainer/devcontainer.json`）で `~/.aws` をマウント
- または `docker-compose.yml` でボリュームマウント設定を追加

### Bootstrap失敗時の確認事項
1. AWS認証情報が正しく設定されているか確認
   ```bash
   aws sts get-caller-identity
   ```
2. 必要なIAM権限があるか確認
3. リージョンが正しく指定されているか確認
   ```bash
   echo $AWS_REGION
   ```

### CDK CLIが見つからない場合
コンテナイメージの再ビルドが必要な可能性があります：
```bash
# コンテナから一度退出
exit

# コンテナの再ビルド
docker-compose build --no-cache

# コンテナの再起動
docker-compose up -d
```

## 次のステップ
事前準備完了後、フェーズ1（基盤セットアップ）に進みます。
フェーズ1では、CDKプロジェクトの初期化と環境設定ファイルの作成を行います。

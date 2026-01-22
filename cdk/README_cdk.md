# CDK デプロイ手順

このドキュメントでは、コンテナ環境内でAWS CDKを使用してインフラをデプロイする手順を説明します。

## 目次
- [前提条件](#前提条件)
- [環境構築](#環境構築)
- [デプロイ手順](#デプロイ手順)
- [環境別デプロイ](#環境別デプロイ)
- [よく使うコマンド](#よく使うコマンド)
- [トラブルシューティング](#トラブルシューティング)

## 前提条件

### 必要なツール
- Docker Desktop
- Visual Studio Code
- VSCode拡張機能: Dev Containers

### AWS認証情報の設定
ローカルマシンの `~/.aws/` ディレクトリに認証情報が設定されている必要があります。

```bash
# ~/.aws/credentials
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY

# 複数プロファイルを使用する場合
[dev]
aws_access_key_id = YOUR_DEV_ACCESS_KEY
aws_secret_access_key = YOUR_DEV_SECRET_KEY

[prod]
aws_access_key_id = YOUR_PROD_ACCESS_KEY
aws_secret_access_key = YOUR_PROD_SECRET_KEY

# ~/.aws/config
[default]
region = ap-northeast-1

[profile dev]
region = ap-northeast-1

[profile prod]
region = ap-northeast-1
```

## 環境構築

### 1. DevContainerを起動

#### VSCodeから起動する場合
1. VSCodeでプロジェクトルートを開く
2. コマンドパレット（Cmd+Shift+P / Ctrl+Shift+P）を開く
3. "Dev Containers: Reopen in Container" を選択
4. "CDK (AWS Infrastructure)" を選択

#### docker-composeから起動する場合
```bash
# プロジェクトルートで実行
docker-compose --profile cdk up -d cdk
docker-compose exec cdk bash
```

### 2. 依存関係のインストール確認
DevContainer起動時に自動でインストールされますが、手動で確認・インストールする場合:

```bash
cd /cdk
npm install
```

### 3. AWS認証情報とプロファイルの設定

#### AWS_PROFILEの設定
使用するAWSプロファイルを環境変数で設定します。

```bash
# デフォルトプロファイルを使用する場合（設定不要）
aws sts get-caller-identity

# 開発環境用プロファイルを使用する場合
export AWS_PROFILE=dev
aws sts get-caller-identity

# 本番環境用プロファイルを使用する場合
export AWS_PROFILE=prod
aws sts get-caller-identity
```

#### プロファイルの永続化（推奨）
セッション中、常に同じプロファイルを使用する場合は、`.bashrc`や`.zshrc`に追加:

```bash
# コンテナ内で設定
echo 'export AWS_PROFILE=dev' >> ~/.bashrc
source ~/.bashrc
```

#### 認証情報の確認
正常に設定されている場合、AWSアカウントIDとユーザー情報が表示されます:

```bash
aws sts get-caller-identity
# 出力例:
# {
#     "UserId": "AIDAXXXXXXXXXXXXXXXXX",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/your-username"
# }
```

## デプロイ手順

### 0. AWS_PROFILEの設定（重要）
デプロイ前に必ず正しいプロファイルを設定してください。

```bash
# 開発環境にデプロイする場合
export AWS_PROFILE=dev

# 本番環境にデプロイする場合
export AWS_PROFILE=prod

# 設定確認
echo $AWS_PROFILE
aws sts get-caller-identity
```

### 1. CDKのブートストラップ（初回のみ）
AWSアカウント・リージョンで初めてCDKを使用する場合、ブートストラップが必要です。

```bash
# 開発環境用
export AWS_PROFILE=dev
cdk bootstrap aws://ACCOUNT-ID/ap-northeast-1

# 本番環境用
export AWS_PROFILE=prod
cdk bootstrap aws://ACCOUNT-ID/ap-northeast-1
```

環境変数を使用する場合:
```bash
export AWS_PROFILE=dev
cdk bootstrap aws://$CDK_DEFAULT_ACCOUNT/$AWS_REGION
```

### 2. TypeScriptのビルド
```bash
npm run build
```

### 3. CDK差分確認
デプロイ前に変更内容を確認:

```bash
# 開発環境の差分確認
export AWS_PROFILE=dev
cdk diff -c env=dev

# 本番環境の差分確認
export AWS_PROFILE=prod
cdk diff -c env=prod
```

### 4. CloudFormationテンプレートの生成（オプション）
```bash
# 開発環境
cdk synth -c env=dev

# 本番環境
cdk synth -c env=prod
```

### 5. デプロイ実行
```bash
# 開発環境へのデプロイ
export AWS_PROFILE=dev
cdk deploy -c env=dev --all

# 本番環境へのデプロイ
export AWS_PROFILE=prod
cdk deploy -c env=prod --all

# 特定のスタックのみデプロイ
cdk deploy -c env=dev NetworkStack-dev

# 承認プロンプトをスキップ（CI/CD環境用）
cdk deploy -c env=dev --all --require-approval never
```

### 6. デプロイ結果の確認
デプロイが完了すると、以下の情報が表示されます:
- スタック名
- 作成されたリソースのARN
- 出力値（Outputs）

## 環境別デプロイ

このプロジェクトでは、環境ごとに異なる設定を使用します。

### 開発環境（dev）
```bash
# プロファイル設定
export AWS_PROFILE=dev

# デプロイ
cdk deploy -c env=dev --all
```

開発環境の特徴:
- コスト最適化された構成
- VPCエンドポイント使用（NAT Gatewayなし）
- リソースの削除ポリシー: DESTROY
- バックアップ保持期間: 短め

### 本番環境（prod）
```bash
# プロファイル設定
export AWS_PROFILE=prod

# デプロイ
cdk deploy -c env=prod --all
```

本番環境の特徴:
- 高可用性構成
- マルチAZ配置
- リソースの削除ポリシー: RETAIN/SNAPSHOT
- バックアップ保持期間: 長め
- 削除保護有効

## よく使うコマンド

### 現在のプロファイル確認
```bash
echo $AWS_PROFILE
aws sts get-caller-identity
```

### プロファイルの切り替え
```bash
# 開発環境に切り替え
export AWS_PROFILE=dev

# 本番環境に切り替え
export AWS_PROFILE=prod

# デフォルトに戻す
unset AWS_PROFILE
```

### スタック一覧の確認
```bash
cdk list -c env=dev
```

### スタックの削除
```bash
# 開発環境のスタック削除
export AWS_PROFILE=dev
cdk destroy -c env=dev --all

# 特定のスタックのみ削除
cdk destroy -c env=dev NetworkStack-dev
```

### コードの自動ビルド（開発時）
```bash
npm run watch
```

### テストの実行
```bash
npm test
```

### CDKバージョンの確認
```bash
cdk --version
```

## デプロイの流れ（推奨手順）

```bash
# 1. プロファイルの設定と確認
export AWS_PROFILE=dev
aws sts get-caller-identity

# 2. コードをビルド
npm run build

# 3. 変更内容を確認
cdk diff -c env=dev --all

# 4. CloudFormationテンプレートを確認（オプション）
cdk synth -c env=dev

# 5. デプロイ実行
cdk deploy -c env=dev --all

# 6. デプロイ後の確認
aws cloudformation describe-stacks --stack-name NetworkStack-dev
```

## トラブルシューティング

### AWS_PROFILEが設定されていない
```bash
# 現在のプロファイルを確認
echo $AWS_PROFILE

# プロファイルを設定
export AWS_PROFILE=dev

# 確認
aws sts get-caller-identity
```

### 誤ったプロファイルでデプロイしそうになった
```bash
# デプロイ前に必ず確認
echo "現在のプロファイル: $AWS_PROFILE"
aws sts get-caller-identity
```

出力されたアカウントIDが正しいか確認してからデプロイしてください。

### AWS認証エラー
```bash
# 認証情報の確認
aws sts get-caller-identity

# AWS CLI設定の確認
aws configure list

# プロファイル別の設定確認
aws configure list --profile dev
aws configure list --profile prod
```

対処法:
- ホストマシンの `~/.aws/` ディレクトリに正しい認証情報があるか確認
- プロファイル名が正しいか確認
- DevContainerを再起動してマウントをやり直す

### ブートストラップエラー
```bash
Unable to resolve AWS account to use
```

対処法:
```bash
# プロファイルを設定してから実行
export AWS_PROFILE=dev
cdk bootstrap aws://123456789012/ap-northeast-1
```

### ビルドエラー
```bash
# node_modulesを削除して再インストール
rm -rf node_modules package-lock.json
npm install
npm run build
```

### デプロイ失敗時のロールバック
CDKは自動的にロールバックしますが、手動で確認する場合:
```bash
# CloudFormationスタックの状態確認
aws cloudformation describe-stack-events --stack-name NetworkStack-dev --max-items 20
```

### スタックが削除できない
```bash
# 正しいプロファイルを設定
export AWS_PROFILE=dev

# 削除保護を無効化してから削除
aws cloudformation update-termination-protection \
  --stack-name NetworkStack-dev \
  --no-enable-termination-protection

cdk destroy -c env=dev NetworkStack-dev
```

## 安全なデプロイのためのチェックリスト

デプロイ前に以下を確認してください:

- [ ] `AWS_PROFILE` が正しく設定されているか
  ```bash
  echo $AWS_PROFILE
  ```
- [ ] 認証情報が正しいアカウントを指しているか
  ```bash
  aws sts get-caller-identity
  ```
- [ ] デプロイ先の環境が正しいか（`-c env=dev` または `-c env=prod`）
- [ ] コードがビルドされているか
  ```bash
  npm run build
  ```
- [ ] 差分を確認したか
  ```bash
  cdk diff -c env=dev --all
  ```

## 設定ファイル

環境別の設定は以下のファイルで管理されています:
- [lib/config/dev.ts](lib/config/dev.ts) - 開発環境設定
- [lib/config/prod.ts](lib/config/prod.ts) - 本番環境設定
- [lib/config/env-config.ts](lib/config/env-config.ts) - 設定のインターフェース定義

## CI/CDでの使用

CI/CD環境でデプロイする場合の例:

```bash
#!/bin/bash
set -e

# プロファイル設定（CI/CD環境では通常不要）
# export AWS_PROFILE=dev

# 依存関係インストール
npm ci

# ビルド
npm run build

# テスト
npm test

# デプロイ（承認プロンプトなし）
cdk deploy -c env=dev --all --require-approval never
```

CI/CD環境では、通常IAMロールを使用するため`AWS_PROFILE`の設定は不要です。

## 参考リンク
- [AWS CDK公式ドキュメント](https://docs.aws.amazon.com/cdk/)
- [AWS CDK API リファレンス](https://docs.aws.amazon.com/cdk/api/v2/)
- [CDK Best Practices](https://docs.aws.amazon.com/cdk/v2/guide/best-practices.html)
- [AWS CLI Named Profiles](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-profiles.html)

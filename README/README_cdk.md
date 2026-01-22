# CDK開発環境ガイド

## CDKの立ち上げ方

### 1. Dev Containerで開く
VSCodeで `cdk` フォルダを開き、「Dev Containerで再度開く」を選択します。

CDKサービスが起動します。

### 2. 依存関係のインストール
Dev Container作成時に `postCreateCommand` が自動実行され、依存関係がインストールされます。

手動でインストールする場合：
```bash
npm install
```

### 3. AWS認証情報の確認
CDK Dev Containerは、ホストの `~/.aws` ディレクトリをマウントしています。

AWS認証情報を確認：
```bash
aws configure list
```

認証情報が未設定の場合は、ホスト側で設定してください：
```bash
# ホストマシンで実行
aws configure
```

## Dev Container内でできること

### 1. CDKコマンド

#### CDKアプリケーションの初期化（初回のみ）
```bash
cdk init app --language=typescript
```

#### CDKスタックのリスト表示
```bash
cdk list
# または
cdk ls
```

#### CDKスタックの差分確認
```bash
cdk diff
```

#### CloudFormationテンプレートの生成
```bash
cdk synth
```

生成されたテンプレートは `cdk.out/` ディレクトリに出力されます。

#### CDKスタックのデプロイ
```bash
# 全スタックをデプロイ
cdk deploy

# 特定のスタックをデプロイ
cdk deploy <stack-name>

# 承認なしでデプロイ
cdk deploy --require-approval never

# すべての変更を自動承認
cdk deploy --all --require-approval never
```

#### CDKスタックの削除
```bash
# 全スタックを削除
cdk destroy

# 特定のスタックを削除
cdk destroy <stack-name>

# 承認なしで削除
cdk destroy --force
```

#### CDK Bootstrapの実行
CDKを初めて使用するAWSアカウント・リージョンでは、Bootstrapが必要です：
```bash
cdk bootstrap aws://ACCOUNT-ID/REGION
```

例：
```bash
cdk bootstrap aws://123456789012/ap-northeast-1
```

### 2. TypeScriptのビルドとテスト

#### TypeScriptのコンパイル
```bash
npm run build
```

#### TypeScriptの監視モード（自動コンパイル）
```bash
npm run watch
```

#### テストの実行
```bash
npm test
```

### 3. コードフォーマット・リント

#### ESLintでチェック
```bash
npx eslint . --ext .ts
```

#### ESLintで自動修正
```bash
npx eslint . --ext .ts --fix
```

#### Prettierでフォーマット
```bash
npx prettier --write "**/*.ts"
```

> **Note:** Dev Containerでは保存時に自動フォーマットが有効になっています

### 4. AWS CLIコマンド

Dev Container内でAWS CLIも使用できます。

#### CloudFormationスタックの確認
```bash
aws cloudformation list-stacks
```

#### 特定のスタックの詳細を確認
```bash
aws cloudformation describe-stacks --stack-name <stack-name>
```

#### リソースの確認
```bash
# ECSクラスター一覧
aws ecs list-clusters

# RDS一覧
aws rds describe-db-instances
```

## プロジェクト構造

```
cdk/
├── bin/                       # CDKアプリケーションのエントリーポイント
├── lib/                       # CDKスタック定義
├── test/                      # テストコード
├── .devcontainer/             # Dev Container設定
├── package.json               # プロジェクト設定と依存関係
├── tsconfig.json              # TypeScript設定
├── cdk.json                   # CDK設定
└── Dockerfile                 # Docker設定
```

## トラブルシューティング

### 依存関係の問題
```bash
# node_modulesを削除して再インストール
rm -rf node_modules package-lock.json
npm install
```

### CDK Bootstrapエラー
```bash
# Bootstrapスタックの状態を確認
aws cloudformation describe-stacks --stack-name CDKToolkit

# Bootstrapを再実行
cdk bootstrap --force
```

### AWS認証エラー
```bash
# 認証情報を確認
aws sts get-caller-identity

# 認証情報が正しくない場合は、ホスト側で再設定
# ホストマシンで実行:
aws configure
```

### Dev Containerの再ビルド
1. コマンドパレット（Cmd+Shift+P / Ctrl+Shift+P）を開く
2. 「Dev Containers: Rebuild Container」を選択
3. コンテナが再ビルドされ、依存関係が再インストールされます

## ベストプラクティス

### 1. スタック設計
- 環境ごとにスタックを分ける（dev, staging, prod）
- リソースの依存関係を明確にする
- タグを適切に設定する

### 2. セキュリティ
- シークレット情報はSecrets ManagerまたはParameter Storeに保存
- IAMロールは最小権限の原則に従う
- VPCやセキュリティグループを適切に設定

### 3. コスト管理
- 不要なリソースは削除する
- 開発環境は小さいインスタンスタイプを使用
- タグでコスト追跡を行う

### 4. デプロイフロー
```bash
# 1. 差分を確認
cdk diff

# 2. テンプレートを生成
cdk synth

# 3. デプロイ
cdk deploy

# 4. デプロイ後の確認
aws cloudformation describe-stacks --stack-name <stack-name>
```

## 参考リンク

- AWS CDK公式ドキュメント: https://docs.aws.amazon.com/cdk/
- AWS CDK API Reference: https://docs.aws.amazon.com/cdk/api/v2/
- AWS CDK Examples: https://github.com/aws-samples/aws-cdk-examples
- AWS CLI Reference: https://docs.aws.amazon.com/cli/



<!-- export AWS_PROFILE=takahata && export AWS_REGION=ap-northeast-1 && cdk destroy NetworkStack-dev --context env=dev --force
5  cdk synth SecurityStack-dev -c env=dev
6  cdk deploy SecurityStack-dev -c env=dev -->
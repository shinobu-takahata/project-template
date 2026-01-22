# フェーズ0: 事前準備 - タスクリスト

## 概要
このタスクリストは、AWS CDK実装の事前準備として必要な環境確認とセットアップ作業を定義します。

## タスク一覧

### 1. CDK開発コンテナ環境の確認
- [ ] **1.1** CDK開発コンテナが起動していることを確認
- [ ] **1.2** コンテナ内でNode.jsバージョン確認（`node --version`）→ v18以上であること
- [ ] **1.3** コンテナ内でnpmバージョン確認（`npm --version`）→ v8以上であること
- [ ] **1.4** コンテナ内でAWS CLIバージョン確認（`aws --version`）→ v2であること
- [ ] **1.5** コンテナ内でCDK CLIバージョン確認（`cdk --version`）→ v2であること

**完了条件**: すべてのツールが正しいバージョンでインストールされていること

---

### 2. AWS認証情報の確認
- [ ] **2.1** AWS認証情報がコンテナ内で利用可能であることを確認（`~/.aws` マウント確認）
- [ ] **2.2** AWS CLIで認証情報を確認（`aws configure list`）
- [ ] **2.3** アカウントIDを取得（`aws sts get-caller-identity`）
- [ ] **2.4** リージョン設定を確認（`aws configure get region`）→ ap-northeast-1が推奨
- [ ] **2.5** 必要なIAM権限があることを確認（CloudFormation、IAM、S3、ECR等）

**完了条件**: AWS CLIでアカウント情報が正常に取得でき、必要な権限があること

---

### 3. AWS CDK Bootstrapの実行
- [ ] **3.1** アカウントIDを環境変数に設定
  ```bash
  export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
  echo $AWS_ACCOUNT_ID
  ```
- [ ] **3.2** CDK Bootstrap実行
  ```bash
  cdk bootstrap aws://${AWS_ACCOUNT_ID}/ap-northeast-1
  ```
- [ ] **3.3** CloudFormation Stackの作成確認
  ```bash
  aws cloudformation describe-stacks \
    --stack-name CDKToolkit \
    --region ap-northeast-1 \
    --query 'Stacks[0].StackStatus' \
    --output text
  ```
  期待される出力: `CREATE_COMPLETE` または `UPDATE_COMPLETE`
- [ ] **3.4** S3バケットの作成確認
  ```bash
  aws s3 ls | grep cdk
  ```
  期待される出力: `cdk-*-assets-{ACCOUNT-ID}-ap-northeast-1`
- [ ] **3.5** ECRリポジトリの作成確認
  ```bash
  aws ecr describe-repositories \
    --region ap-northeast-1 \
    --query 'repositories[?contains(repositoryName, `cdk`)].repositoryName'
  ```
  期待される出力: `cdk-*-container-assets-{ACCOUNT-ID}-ap-northeast-1`

**完了条件**: Bootstrap用のCloudFormation Stack、S3バケット、ECRリポジトリが正常に作成されていること

---

### 4. GitHub Personal Access Tokenの発行
- [ ] **4.1** GitHubにログイン
- [ ] **4.2** Settings → Developer settings → Personal access tokens → Tokens (classic) に移動
- [ ] **4.3** "Generate new token (classic)" をクリック
- [ ] **4.4** トークン設定:
  - Note: `CDK CI/CD Pipeline`
  - Expiration: 90日以上
  - Scopes: `repo` にチェック
- [ ] **4.5** "Generate token" をクリック
- [ ] **4.6** 表示されたトークンをコピー（**重要**: 再表示不可）
- [ ] **4.7** トークンを安全な場所に保管
  - パスワードマネージャーに保存
  - または環境変数として設定（`.env`ファイルなど、`.gitignore`に追加済みであること）

**完了条件**: GitHub Personal Access Tokenが発行され、安全に保管されていること

---

### 5. 環境確認レポートの作成（任意）
- [ ] **5.1** 確認結果をまとめたレポート作成（テキストファイルまたはメモ）
  - Node.js、npm、AWS CLI、CDK CLIのバージョン
  - AWSアカウントID
  - Bootstrapされたリージョン
  - Bootstrap作成リソース（Stack名、S3バケット名、ECRリポジトリ名）
  - GitHub Personal Access Token発行日

**完了条件**: 環境確認結果が記録されていること

---

## 全体の完了条件

以下のすべてが満たされていること：
- [ ] CDK開発コンテナ環境が正しくセットアップされている
- [ ] AWS認証情報がコンテナ内で利用可能
- [ ] ap-northeast-1リージョンでCDK Bootstrapが完了している
- [ ] GitHub Personal Access Tokenが発行され、安全に保管されている

## トラブルシューティング

### AWS認証エラーが発生する場合
1. コンテナの `~/.aws` ディレクトリマウント確認
2. 環境変数 `AWS_ACCESS_KEY_ID`、`AWS_SECRET_ACCESS_KEY`、`AWS_REGION` 確認
3. ホスト側の AWS CLI 設定確認

### Bootstrap失敗時
1. IAM権限の確認（CloudFormation、IAM、S3、ECR へのアクセス権限）
2. リージョン設定の確認
3. エラーメッセージの詳細を確認し、必要に応じて権限を追加

### CDK CLIが見つからない場合
1. コンテナイメージの再ビルド
2. Dockerfileの確認（CDK CLIのインストール手順）

## 次のステップ
すべてのタスクが完了したら、フェーズ1（基盤セットアップ）に進みます。

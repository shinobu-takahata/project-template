---
name: cdk-deploy
description: "AWS CDKでインフラをデプロイするときに使うスキル。AWSプロファイルの確認・ビルド・差分確認・デプロイを安全な順番でガイドする。「CDKをデプロイしたい」「インフラを反映したい」「cdk deployしたい」「スタックを更新したい」と言ったときに必ず使う。誤った環境へのデプロイを防ぐためのセーフティチェックを含む。"
---

# CDK Deploy

AWS CDKのデプロイは**誤った環境（本番/開発）に適用すると取り返しがつかない**ことがある。
このフローに従って慎重に進める。

---

## Step 1: デプロイ対象の環境を確認する

まずユーザーに確認する:
- **どの環境にデプロイするか？** `dev` / `prod`
- **特定のスタックのみか、全スタックか？**（デフォルトは `--all`）

---

## Step 2: AWS プロファイルを確認・設定する

```bash
# 現在のプロファイル確認
echo "現在のAWS_PROFILE: $AWS_PROFILE"

# 正しいプロファイルを設定
export AWS_PROFILE=dev   # または prod

# 認証情報とアカウントIDを確認（必ず実行する）
aws sts get-caller-identity
```

出力されたアカウントIDが**目的の環境のもの**であることをユーザーに確認してもらう。
**アカウントIDが正しくない場合は絶対に先に進まない。**

---

## Step 3: ビルドする

```bash
cd cdk
npm run build
```

TypeScriptのコンパイルエラーがないことを確認する。

---

## Step 4: 差分を確認する（必須）

デプロイ前に変更内容を必ず確認する:

```bash
# 全スタック
cdk diff -c env=dev --all   # または env=prod

# 特定のスタックのみ
cdk diff -c env=dev NetworkStack-dev
```

差分の内容をユーザーに説明する。特に以下は注意して伝える:
- リソースの**削除**が含まれる場合（データ損失の可能性）
- セキュリティグループ・IAMポリシーの変更
- `RETAIN` / `DESTROY` 削除ポリシーを持つリソースの変更

**破壊的な変更がある場合は、ユーザーに明示的に確認を取る。**

---

## Step 5: デプロイ実行

差分をユーザーが確認・承認したらデプロイする:

```bash
# 全スタックをデプロイ
export AWS_PROFILE=dev
cdk deploy -c env=dev --all

# 特定のスタックのみ
cdk deploy -c env=dev NetworkStack-dev

# CI/CD環境（承認プロンプトなし）
cdk deploy -c env=dev --all --require-approval never
```

---

## Step 6: デプロイ結果の確認

デプロイ完了後:
1. 出力された Outputs（ARN、エンドポイント等）を確認
2. 必要に応じて CloudFormation コンソールで状態確認:
   ```bash
   aws cloudformation describe-stacks --stack-name [スタック名]
   ```

---

## よく使うコマンドリファレンス

```bash
# スタック一覧
cdk list -c env=dev

# CloudFormationテンプレート生成（デプロイなし）
cdk synth -c env=dev

# スタック削除（本番では要注意）
export AWS_PROFILE=dev
cdk destroy -c env=dev --all

# プロファイル切り替え
export AWS_PROFILE=dev    # 開発環境
export AWS_PROFILE=prod   # 本番環境
unset AWS_PROFILE         # デフォルトに戻す
```

---

## トラブルシューティング

**認証エラー:**
```bash
aws sts get-caller-identity
aws configure list --profile dev
```
→ ホストの `~/.aws/credentials` を確認。DevContainer使用時はマウントされているか確認。

**ビルドエラー:**
```bash
rm -rf node_modules
npm install
npm run build
```

**スタックが削除できない:**
```bash
# 削除保護を解除してから削除
aws cloudformation update-termination-protection \
  --stack-name [スタック名] \
  --no-enable-termination-protection
```

**Bootstrap未実施エラー:**
```bash
cdk bootstrap aws://[AWSアカウントID]/ap-northeast-1
```

---

## デプロイ前チェックリスト

デプロイ実行前に以下を必ず確認:
- [ ] `AWS_PROFILE` が正しい環境を指している
- [ ] `aws sts get-caller-identity` のアカウントIDが正しい
- [ ] `npm run build` が成功している
- [ ] `cdk diff` で変更内容を確認した
- [ ] 破壊的変更がある場合、ユーザーの明示的な承認を得た

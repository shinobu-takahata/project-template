# フェーズ4.5: ECRスタック - タスクリスト

## タスク一覧

### 1. EcrStack基本構造の作成
- [ ] `lib/stacks/ecr-stack.ts` ファイルの作成
- [ ] EcrStackPropsインターフェースの定義
- [ ] 必要なインポートの追加
- [ ] EcrStackクラスの基本構造実装

### 2. ECRリポジトリの実装
- [ ] ECRリポジトリの作成（repositoryName設定）
- [ ] イメージスキャン設定（imageScanOnPush: true）
- [ ] タグ変更可否設定（imageTagMutability）
- [ ] ライフサイクルポリシーの設定（maxImageCount: 10）
- [ ] 暗号化設定（AES_256）
- [ ] RemovalPolicy設定（RETAIN）

### 3. CfnOutputの実装
- [ ] EcrRepositoryUriのエクスポート
- [ ] EcrRepositoryArnのエクスポート
- [ ] EcrRepositoryNameのエクスポート

### 4. app.tsの更新
- [ ] EcrStackのインポート追加
- [ ] EcrStackのインスタンス化
- [ ] ComputeStackへの依存関係設定（computeStack.addDependency(ecrStack)）

### 5. ビルド・検証
- [ ] TypeScriptコンパイル (`npm run build`)
- [ ] CDK Synth (`cdk synth EcrStack-dev --context env=dev`)
- [ ] エラーがないことの確認

### 6. デプロイ検証（オプション）
- [ ] EcrStackのデプロイ (`cdk deploy EcrStack-dev --context env=dev`)
- [ ] ECRリポジトリの作成確認
- [ ] CloudFormation Exportsの確認

## 進捗状況
- 開始日: 2026-01-26
- 完了日: -
- ステータス: 未着手

## 備考
- このスタックは他のスタックに依存しない
- ComputeStack実装前にデプロイ可能
- 初回デプロイ後、手動でダミーイメージをプッシュする必要がある

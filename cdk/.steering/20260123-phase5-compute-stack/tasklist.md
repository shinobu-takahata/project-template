# フェーズ5: コンピューティング基盤 - タスクリスト

## タスク一覧

### 1. ComputeStack基本構造の作成
- [ ] `lib/stacks/compute-stack.ts` ファイルの作成
- [ ] ComputeStackPropsインターフェースの定義
- [ ] 必要なインポートの追加
- [ ] VPC、Secrets Manager ARN、WebAcl ARN、ECRリポジトリURIのインポート

### 2. S3バケット（ALBアクセスログ用）の実装
- [ ] ALBアクセスログ用S3バケットの作成
- [ ] バケットポリシーの設定（ALBからのアクセス許可）
- [ ] ライフサイクルポリシーの設定

### 3. セキュリティグループの実装
- [ ] ALB用セキュリティグループの作成
- [ ] ECS用セキュリティグループの作成
- [ ] インバウンド/アウトバウンドルールの設定

### 4. ALBの実装
- [ ] Application Load Balancerの作成
- [ ] ターゲットグループの作成
- [ ] HTTPリスナーの作成
- [ ] アクセスログの設定
- [ ] WAFの関連付け

### 5. ECS Clusterの実装
- [ ] ECS Clusterの作成
- [ ] Container Insightsの有効化

### 6. IAMロールの実装
- [ ] タスク実行ロールの作成
- [ ] タスクロールの作成
- [ ] 必要なポリシーのアタッチ

### 7. ECS Task Definitionの実装
- [ ] Fargate Task Definitionの作成
- [ ] メインコンテナ（FastAPI）の追加
- [ ] Fluent Bitサイドカーの追加
- [ ] 環境変数・シークレットの設定

### 8. ECS Serviceの実装
- [ ] Fargate Serviceの作成
- [ ] ALBターゲットグループとの連携
- [ ] Auto Scalingの設定

### 9. スタック出力の実装
- [ ] CfnOutputの追加
- [ ] 必要な値のエクスポート

### 10. app.tsの更新
- [ ] ComputeStackのインポート追加
- [ ] ComputeStackのインスタンス化
- [ ] スタック依存関係の設定

### 11. ビルド・検証
- [ ] TypeScriptコンパイル (`npm run build`)
- [ ] CDK Synth (`cdk synth`)
- [ ] エラーがないことの確認

## 進捗状況
- 開始日: 2026-01-23
- 完了日: -
- ステータス: 未着手

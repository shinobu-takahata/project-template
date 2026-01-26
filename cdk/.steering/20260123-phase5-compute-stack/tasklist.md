# フェーズ5: コンピューティング基盤 - タスクリスト

## タスク一覧

### 1. ComputeStack基本構造の作成
- [ ] `lib/stacks/compute-stack.ts` ファイルの作成
- [ ] ComputeStackPropsインターフェースの定義
- [ ] 必要なインポートの追加
- [ ] VPC、Secrets Manager ARN、WebAcl ARNのインポート

### 2. ECRリポジトリの実装
- [ ] ECRリポジトリの作成
- [ ] イメージスキャン設定
- [ ] ライフサイクルポリシーの設定
- [ ] 暗号化設定

### 3. S3バケット（ALBアクセスログ用）の実装
- [ ] ALBアクセスログ用S3バケットの作成
- [ ] バケットポリシーの設定（ALBからのアクセス許可）
- [ ] ライフサイクルポリシーの設定

### 4. セキュリティグループの実装
- [ ] ALB用セキュリティグループの作成
- [ ] ECS用セキュリティグループの作成
- [ ] インバウンド/アウトバウンドルールの設定

### 5. ALBの実装
- [ ] Application Load Balancerの作成
- [ ] ターゲットグループの作成
- [ ] HTTPリスナーの作成
- [ ] アクセスログの設定
- [ ] WAFの関連付け

### 6. ECS Clusterの実装
- [ ] ECS Clusterの作成
- [ ] Container Insightsの有効化

### 7. IAMロールの実装
- [ ] タスク実行ロールの作成
- [ ] タスクロールの作成
- [ ] 必要なポリシーのアタッチ

### 8. ECS Task Definitionの実装
- [ ] Fargate Task Definitionの作成
- [ ] メインコンテナ（FastAPI）の追加
- [ ] Fluent Bitサイドカーの追加
- [ ] 環境変数・シークレットの設定

### 9. ECS Serviceの実装
- [ ] Fargate Serviceの作成
- [ ] ALBターゲットグループとの連携
- [ ] Auto Scalingの設定

### 10. スタック出力の実装
- [ ] CfnOutputの追加
- [ ] 必要な値のエクスポート

### 11. app.tsの更新
- [ ] ComputeStackのインポート追加
- [ ] ComputeStackのインスタンス化
- [ ] スタック依存関係の設定

### 12. ビルド・検証
- [ ] TypeScriptコンパイル (`npm run build`)
- [ ] CDK Synth (`cdk synth`)
- [ ] エラーがないことの確認

## 進捗状況
- 開始日: 2026-01-23
- 完了日: -
- ステータス: 未着手

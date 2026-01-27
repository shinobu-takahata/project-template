# タスクリスト: FireLensとFluent Bitを使用したログルーティング機能の実装

## タスク一覧

### フェーズ1: Fluent Bit設定ファイルの作成

- [ ] **タスク1.1: Fluent Bitディレクトリ構造の作成**
  - `cdk/docker/fluent-bit/` ディレクトリを作成
  - 依存関係: なし
  - 所要時間: 5分

- [ ] **タスク1.2: Dockerfileの作成**
  - ベースイメージ: `public.ecr.aws/aws-observability/aws-for-fluent-bit:latest`
  - 設定ファイルをコピー
  - ヘルスチェックを設定
  - ファイルパス: `cdk/docker/fluent-bit/Dockerfile`
  - 依存関係: タスク1.1
  - 所要時間: 15分

- [ ] **タスク1.3: parsers.confの作成**
  - JSON形式のログパーサーを定義
  - Time_KeyとTime_Formatを設定
  - ファイルパス: `cdk/docker/fluent-bit/parsers.conf`
  - 依存関係: タスク1.1
  - 所要時間: 10分

- [ ] **タスク1.4: fluent-bit.confの作成**
  - [SERVICE]セクション: Flush間隔、ログレベル、パーサーファイル指定
  - [INPUT]セクション: Forwardプロトコルでポート24224をリッスン
  - [FILTER]セクション: JSONパーサー適用
  - [OUTPUT]セクション1: CloudWatch Logs（ERRORレベル以上）
  - [OUTPUT]セクション2: S3（全ログ）
  - 環境変数の使用: `${AWS_REGION}`、`${LOG_BUCKET_NAME}`
  - ファイルパス: `cdk/docker/fluent-bit/fluent-bit.conf`
  - 依存関係: タスク1.3
  - 所要時間: 30分

- [ ] **タスク1.5: Fluent Bit設定の構文チェック**
  - `fluent-bit -c fluent-bit.conf --dry-run` でテスト
  - 構文エラーがないことを確認
  - 依存関係: タスク1.4
  - 所要時間: 10分

### フェーズ2: カスタムFluent BitイメージのビルドとECRプッシュ

- [ ] **タスク2.1: Fluent Bit用ECRリポジトリの作成（CDK）**
  - `cdk/lib/stacks/compute-stack.ts` を編集
  - `ecr.Repository` を作成: リポジトリ名 `fluent-bit-custom`
  - イメージスキャンを有効化
  - ライフサイクルポリシー: 最新5イメージ保持
  - 依存関係: なし
  - 所要時間: 15分

- [ ] **タスク2.2: CDKデプロイ（ECRリポジトリのみ）**
  - `cdk deploy ComputeStack-dev --context env=dev` を実行
  - ECRリポジトリが作成されることを確認
  - 依存関係: タスク2.1
  - 所要時間: 5分（デプロイ時間含む）

- [ ] **タスク2.3: ローカルでFluent Bitイメージのビルド**
  - `cd cdk/docker/fluent-bit`
  - `docker build -t fluent-bit-custom:latest .`
  - ビルドが成功することを確認
  - 依存関係: タスク1.5、タスク2.2
  - 所要時間: 10分

- [ ] **タスク2.4: ECRへのログイン**
  - `aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com`
  - 認証が成功することを確認
  - 依存関係: タスク2.2
  - 所要時間: 5分

- [ ] **タスク2.5: イメージのタグ付けとプッシュ**
  - `docker tag fluent-bit-custom:latest <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com/fluent-bit-custom:latest`
  - `docker push <account-id>.dkr.ecr.ap-northeast-1.amazonaws.com/fluent-bit-custom:latest`
  - ECRリポジトリにイメージが表示されることを確認
  - 依存関係: タスク2.3、タスク2.4
  - 所要時間: 10分

### フェーズ3: CDKコードの変更

- [ ] **タスク3.1: MonitoringStackでS3ログバケットの作成/参照**
  - `cdk/lib/stacks/monitoring-stack.ts` を確認
  - S3ログバケットが既に作成されている場合は参照のみ
  - 未作成の場合は新規作成（バケットポリシー、ライフサイクルポリシー含む）
  - 依存関係: なし
  - 所要時間: 15分

- [ ] **タスク3.2: MonitoringStackでCloudWatch Logsロググループの作成**
  - `/ecs/backend/errors` ロググループを作成（既存の場合はスキップ）
  - `/ecs/firelens` ロググループを作成（Fluent Bit自体のログ用）
  - 保持期間: 7日（dev）、30日（prod）
  - ファイルパス: `cdk/lib/stacks/monitoring-stack.ts`
  - 依存関係: なし
  - 所要時間: 10分

- [ ] **タスク3.3: ComputeStackでFluent Bit ECRリポジトリの参照**
  - タスク2.1で作成したECRリポジトリを参照
  - `ecr.Repository.fromRepositoryName()` を使用
  - ファイルパス: `cdk/lib/stacks/compute-stack.ts`
  - 依存関係: タスク2.1
  - 所要時間: 5分

- [ ] **タスク3.4: ECSタスク定義へのFireLensログルーター追加**
  - `taskDefinition.addFirelensLogRouter()` を使用
  - イメージ: Fluent Bit ECRリポジトリから参照
  - FireLens設定: `type: ecs.FirelensLogRouterType.FLUENTBIT`
  - 環境変数: `AWS_REGION`、`LOG_BUCKET_NAME`
  - ログドライバー: AwsLogDriver（`/ecs/firelens`）
  - メモリ予約: 50MB
  - ファイルパス: `cdk/lib/stacks/compute-stack.ts`
  - 依存関係: タスク3.3
  - 所要時間: 30分

- [ ] **タスク3.5: アプリケーションコンテナのログドライバー変更**
  - 既存のAwsLogDriverをFireLensログドライバーに変更
  - `ecs.LogDrivers.firelens()` を使用
  - オプション: `Name: 'forward'`, `Host: 'log-router'`, `Port: '24224'`, `Retry_Limit: '2'`
  - ファイルパス: `cdk/lib/stacks/compute-stack.ts`
  - 依存関係: タスク3.4
  - 所要時間: 15分

- [ ] **タスク3.6: タスクロールへのS3書き込み権限追加**
  - `logBucket.grantWrite(taskDefinition.taskRole)` を使用
  - または `taskDefinition.taskRole.addToPrincipalPolicy()` で `s3:PutObject` 権限を追加
  - ファイルパス: `cdk/lib/stacks/compute-stack.ts`
  - 依存関係: タスク3.1
  - 所要時間: 10分

- [ ] **タスク3.7: タスクロールへのCloudWatch Logs書き込み権限追加**
  - `taskDefinition.taskRole.addToPrincipalPolicy()` で権限を追加
  - アクション: `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`
  - リソース: `arn:aws:logs:*:*:log-group:/ecs/backend/errors:*`
  - ファイルパス: `cdk/lib/stacks/compute-stack.ts`
  - 依存関係: タスク3.2
  - 所要時間: 10分

- [ ] **タスク3.8: タスク実行ロールへのFluent Bit ECRイメージプル権限追加**
  - `fluentBitRepository.grantPull(taskDefinition.executionRole)` を使用
  - または既存のタスク実行ロールに権限が含まれているか確認
  - ファイルパス: `cdk/lib/stacks/compute-stack.ts`
  - 依存関係: タスク3.3
  - 所要時間: 5分

### フェーズ4: CDKデプロイと動作確認

- [ ] **タスク4.1: CDK差分確認**
  - `cdk diff ComputeStack-dev --context env=dev`
  - `cdk diff MonitoringStack-dev --context env=dev`
  - 変更内容を確認
  - 依存関係: タスク3.8
  - 所要時間: 5分

- [ ] **タスク4.2: MonitoringStackのデプロイ**
  - `cdk deploy MonitoringStack-dev --context env=dev`
  - S3バケットとCloudWatch Logsロググループが作成されることを確認
  - 依存関係: タスク4.1
  - 所要時間: 5分（デプロイ時間含む）

- [ ] **タスク4.3: ComputeStackのデプロイ**
  - `cdk deploy ComputeStack-dev --context env=dev`
  - ECSタスク定義が更新されることを確認
  - 依存関係: タスク4.2
  - 所要時間: 10分（デプロイ時間含む）

- [ ] **タスク4.4: ECSタスクの起動確認**
  - ECSコンソールでタスクが正常に起動しているか確認
  - タスク数が希望数（2）に達しているか確認
  - Fluent Bitコンテナのヘルスチェックが成功しているか確認
  - 依存関係: タスク4.3
  - 所要時間: 10分

- [ ] **タスク4.5: Fluent Bitコンテナのログ確認**
  - CloudWatch Logs `/ecs/firelens` でFluent Bitのログを確認
  - エラーがないことを確認
  - CloudWatch LogsとS3への接続が成功しているか確認
  - 依存関係: タスク4.4
  - 所要時間: 10分

### フェーズ5: ログルーティングの動作確認

- [ ] **タスク5.1: INFOログの送信テスト**
  - FastAPIアプリからINFOレベルのログを出力
  - S3バケットにログファイルが作成されることを確認
  - CloudWatch Logs `/ecs/backend/errors` にログが送信されないことを確認
  - 依存関係: タスク4.5
  - 所要時間: 15分

- [ ] **タスク5.2: ERRORログの送信テスト**
  - FastAPIアプリからERRORレベルのログを出力
  - CloudWatch Logs `/ecs/backend/errors` にログが表示されることを確認
  - S3バケットにログファイルが作成されることを確認
  - 依存関係: タスク5.1
  - 所要時間: 15分

- [ ] **タスク5.3: S3ログファイルの内容確認**
  - S3バケットからログファイルをダウンロード
  - gzip圧縮されていることを確認
  - ログ内容がJSON形式で正しく保存されていることを確認
  - 依存関係: タスク5.2
  - 所要時間: 10分

- [ ] **タスク5.4: S3ログファイルのパーティショニング確認**
  - S3バケットでログファイルパスが `logs/year=YYYY/month=MM/day=DD/hour=HH/` の形式になっているか確認
  - 依存関係: タスク5.3
  - 所要時間: 5分

- [ ] **タスク5.5: CloudWatch Logsのログストリーム確認**
  - `/ecs/backend/errors` ロググループにログストリームが作成されているか確認
  - ログストリームプレフィックスが `fargate-` であることを確認
  - 依存関係: タスク5.2
  - 所要時間: 5分

### フェーズ6: パフォーマンスとリソース使用量の確認

- [ ] **タスク6.1: ECSタスクのメモリ使用量確認**
  - CloudWatch MetricsでECSタスクのメモリ使用量を確認
  - Fluent Bit追加によるメモリ増加が許容範囲内（50MB程度）か確認
  - 依存関係: タスク5.5
  - 所要時間: 10分

- [ ] **タスク6.2: ログ送信遅延の測定**
  - ログ出力からCloudWatch Logs/S3への送信までの遅延を測定
  - 許容範囲（数秒以内）に収まっているか確認
  - 依存関係: タスク5.5
  - 所要時間: 15分

- [ ] **タスク6.3: 高負荷時のログ処理テスト（オプション）**
  - 大量のログを短時間で出力
  - Fluent Bitが正常にログを処理できるか確認
  - メモリ使用量やCPU使用率を監視
  - 依存関係: タスク6.2
  - 所要時間: 30分

### フェーズ7: ドキュメント更新とクリーンアップ

- [ ] **タスク7.1: 永続的ドキュメントの影響確認**
  - `docs/architecture/implements_aws_by_cdk_plan.md` が既にFluent Bitの実装を含んでいるか確認
  - 必要に応じて実装完了の記録を追加
  - 依存関係: タスク6.3
  - 所要時間: 10分

- [ ] **タスク7.2: ステアリングドキュメントの更新**
  - 実装中に発見した問題や変更点を記録
  - 次回の参考情報を追加
  - 依存関係: タスク7.1
  - 所要時間: 15分

- [ ] **タスク7.3: 本番環境へのデプロイ計画**
  - 開発環境での動作確認が完了したら、本番環境へのデプロイ計画を作成
  - デプロイタイミング、ロールバック手順を明確化
  - 依存関係: タスク7.2
  - 所要時間: 20分

## 完了条件

### 必須条件
1. Fluent Bit設定ファイル（Dockerfile、fluent-bit.conf、parsers.conf）が作成されている
2. カスタムFluent BitイメージがECRにプッシュされている
3. CDKコードが更新され、デプロイが成功している
4. ECSタスクが正常に起動し、Fluent Bitコンテナのヘルスチェックが成功している
5. INFOログがS3にのみ送信され、CloudWatch Logsには送信されないことを確認
6. ERRORログがCloudWatch LogsとS3の両方に送信されることを確認
7. S3ログファイルが時間別にパーティショニングされていることを確認
8. Fluent Bitコンテナのメモリ使用量が許容範囲内（50MB程度）であることを確認

### オプション条件
1. 高負荷時のログ処理テストが完了している
2. 本番環境へのデプロイ計画が作成されている

## 推定所要時間
- フェーズ1: 約1時間10分
- フェーズ2: 約45分
- フェーズ3: 約1時間40分
- フェーズ4: 約40分
- フェーズ5: 約50分
- フェーズ6: 約55分（高負荷テストを含む）
- フェーズ7: 約45分

**合計**: 約6時間45分

## リスクと対応策

### リスク1: Fluent Bit設定ファイルの構文エラー
- **影響**: ECSタスクが起動しない
- **対応策**: ローカルで `fluent-bit --dry-run` を実行して構文チェックを行う

### リスク2: IAM権限不足
- **影響**: ログがCloudWatch LogsまたはS3に送信されない
- **対応策**: タスクロールとタスク実行ロールの権限を事前に確認、CloudWatch Logsで権限エラーを確認

### リスク3: メモリ不足
- **影響**: ECSタスクがOOMエラーで終了する
- **対応策**: Fluent Bitのメモリ予約を50MBに設定、必要に応じてタスク全体のメモリを増やす

### リスク4: ログ送信遅延
- **影響**: リアルタイムでログが確認できない
- **対応策**: Fluent BitのFlush間隔を調整（デフォルト5秒）、S3アップロードタイムアウトを調整

### リスク5: S3バケットへのアクセス拒否
- **影響**: ログがS3に保存されない
- **対応策**: バケットポリシーでタスクロールからのアクセスを許可、VPCエンドポイント経由でS3にアクセスできることを確認

## 次のステップ
1. CloudWatch Alarmsの設定（エラーログ検出）
2. S3ログのAthenaクエリ設定（オプション）
3. ログ分析ダッシュボードの作成（QuickSightまたはGrafana）
4. 本番環境へのデプロイ

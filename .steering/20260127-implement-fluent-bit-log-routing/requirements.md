# 要求定義: FireLensとFluent Bitを使用したログルーティング機能の実装

## 概要
ECS FargateタスクにFireLensとFluent Bitを統合し、アプリケーションログを効率的にルーティングする機能を実装します。ERRORレベル以上のログをCloudWatch Logsに送信して即座の分析とアラート対応を可能にし、全レベルのログをS3に送信して長期保存とコスト最適化を実現します。

## 背景
現在のログ戦略では、すべてのログをCloudWatch Logsに送信すると月額コストが高額になります（例: 月間100GBで約$50）。Fluent Bitを使用してログレベルに応じてルーティングすることで、以下のメリットが得られます。

- ERRORレベル以上のみCloudWatch Logsに送信することでコスト削減（約85%削減）
- 全ログをS3に保存することで長期保存コストを最適化（S3はCloudWatch Logsの約1/10のコスト）
- ログの目的別管理（即時対応用とアーカイブ用）

## 受け入れ条件

### 必須条件
- [ ] Fluent Bit設定ファイル（fluent-bit.conf、parsers.conf）が作成されている
- [ ] カスタムFluent BitイメージがビルドされてECRにプッシュされている
- [ ] ECSタスク定義にFireLensログルーター（Fluent Bitコンテナ）が追加されている
- [ ] FastAPIアプリケーションコンテナのログドライバーがFireLens経由に設定されている
- [ ] ERRORレベル以上のログがCloudWatch Logs（`/ecs/backend/errors`）に送信されている
- [ ] 全レベルのログがS3バケット（ログバケット）に送信されている
- [ ] CDKコードでFluent Bit用ECRリポジトリが作成されている
- [ ] CDKコードでタスクロールにS3書き込み権限とCloudWatch Logs書き込み権限が付与されている

### ログ送信の動作確認
- [ ] INFOレベルのログがS3にのみ保存され、CloudWatch Logsには送信されない
- [ ] ERRORレベルのログがCloudWatch LogsとS3の両方に保存される
- [ ] S3ログファイルが圧縮（gzip）されて保存されている
- [ ] S3ログファイルが時間別にパーティショニングされている（year/month/day/hour）

### パフォーマンスと信頼性
- [ ] Fluent Bitコンテナのヘルスチェックが設定されている
- [ ] ログ送信の失敗時にリトライ機能が動作する
- [ ] Fluent Bitコンテナ自体のログがCloudWatch Logs（`/ecs/firelens`）に出力されている

## 制約事項

### 技術的制約
- Fluent Bitバージョン: AWS公式イメージ（`public.ecr.aws/aws-observability/aws-for-fluent-bit:latest`）をベースにする
- ログフォーマット: JSON形式を想定（FastAPI側で構造化ログ出力が必要）
- S3ログファイルサイズ: 100MB単位でローテーション
- ログアップロードタイムアウト: 10分

### セキュリティ制約
- タスクロールにS3バケットへの書き込み権限（PutObject）が必要
- タスクロールにCloudWatch Logsへの書き込み権限（CreateLogGroup、CreateLogStream、PutLogEvents）が必要
- タスク実行ロールにECRからのイメージプル権限が必要

### コスト制約
- CloudWatch Logsの使用量を最小化（ERRORレベル以上のみ）
- S3ストレージコストを考慮（Glacierへの移行、1年後削除）

### 環境制約
- リージョン: ap-northeast-1（東京）
- ECS起動タイプ: Fargate
- ログバケットとCloudWatch Logsロググループが事前に作成されている必要がある

## 依存関係

### 前提条件
- ECS Clusterが作成済み
- ECS Fargate Serviceが作成済み（または作成予定）
- S3ログバケットが作成済み（MonitoringStackで作成）
- CloudWatch Logsロググループ `/ecs/backend/errors` が作成済み
- CloudWatch Logsロググループ `/ecs/firelens` が作成済み（Fluent Bit自体のログ用）

### 後続作業への影響
- CloudWatch Alarmsでエラーログ検出アラームの設定（メトリクスフィルタ使用）
- S3ログのAthenaクエリ設定（オプション）

## 参照ドキュメント
- [AWS CDK 実装計画書 - フェーズ5.4](../../cdk/docs/architecture/implements_aws_by_cdk_plan.md#54-ecs-fargate-servicefastapi--fluent-bit%E3%81%AE%E5%AE%9F%E8%A3%85)
- [Fluent Bit公式ドキュメント - CloudWatch Output](https://docs.fluentbit.io/manual/pipeline/outputs/cloudwatch)
- [Fluent Bit公式ドキュメント - S3 Output](https://docs.fluentbit.io/manual/pipeline/outputs/s3)
- [AWS FireLens公式ドキュメント](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/using_firelens.html)

## 成功基準
1. ローカルでカスタムFluent BitイメージをビルドしてECRにプッシュできる
2. CDKデプロイが成功し、ECSタスクが正常に起動する
3. アプリケーションがINFOログを出力すると、S3にのみ保存される
4. アプリケーションがERRORログを出力すると、CloudWatch LogsとS3の両方に保存される
5. CloudWatch Logsで `/ecs/backend/errors` にERRORログが表示される
6. S3バケットでログファイルが `logs/year=YYYY/month=MM/day=DD/hour=HH/` の形式で保存される
7. Fluent Bitコンテナのヘルスチェックが成功している

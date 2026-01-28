# フェーズ6: 監視とロギング基盤 - 要求仕様書

## 概要
AWS CDK実装計画書のフェーズ6として、監視とロギング基盤（MonitoringStack）を構築する。
CloudWatch Alarms、SNSトピック、CloudWatch Dashboardを新規実装する。

## 参照ドキュメント
- [implements_aws_by_cdk_plan.md](../../docs/architecture/implements_aws_by_cdk_plan.md) - セクション6.1〜6.5
- [aws_infra.md](../../docs/architecture/aws_infra.md) - 監視とロギングセクション

## 実装済み項目（参考）

以下の項目は既存スタックで実装済みのため、MonitoringStackでは作成不要。

### 6.1 S3バケット（ComputeStackで実装済み）
- `app-logs-{envName}-{accountId}` - アプリケーションログ用（Fluent Bit → S3）
- `alb-logs-{envName}-{accountId}` - ALBアクセスログ用

### 6.2 CloudWatch Logs（ComputeStack/NetworkStackで実装済み）
- `/ecs/${envName}/backend` - アプリケーションログ（ComputeStack）
- `/ecs/backend/errors` - エラーログ（ComputeStack）
- `/ecs/firelens` - Fluent Bitログ（ComputeStack）
- `/aws/vpc/flowlogs/${envName}` - VPCフローログ（NetworkStack）

---

## 新規実装要求事項

### 6.3 CloudWatch Alarmsの作成

#### ECS関連アラーム
1. **ERRORログ検出アラーム**
   - メトリクスフィルタで `/ecs/backend/errors` からERRORを検出
   - 閾値: 5分間に5件以上のERROR
   - アクション: critical-alerts SNSトピックへ通知

2. **ECS CPU使用率アラーム**
   - メトリクス: ECSサービスのCPU使用率
   - 閾値: 80%以上が5分間継続
   - アクション: warning-alerts SNSトピックへ通知

3. **ECS メモリ使用率アラーム**
   - メトリクス: ECSサービスのメモリ使用率
   - 閾値: 80%以上が5分間継続
   - アクション: warning-alerts SNSトピックへ通知

4. **ECS タスク起動失敗アラーム**
   - メトリクス: ECSサービスのタスク起動失敗数
   - 閾値: 5分間に3回以上の失敗
   - アクション: critical-alerts SNSトピックへ通知

#### Aurora関連アラーム
1. **Aurora CPU使用率アラーム**
   - メトリクス: Aurora CPUUtilization
   - 閾値: 80%以上が5分間継続
   - アクション: warning-alerts SNSトピックへ通知

2. **Aurora ディスク使用率アラーム**
   - メトリクス: Aurora FreeableMemory
   - 閾値: 利用可能メモリが1GB未満
   - アクション: warning-alerts SNSトピックへ通知

3. **Aurora 接続数アラーム**
   - メトリクス: Aurora DatabaseConnections
   - 閾値: インスタンスクラスに応じた値（例: 80接続以上）
   - アクション: warning-alerts SNSトピックへ通知

4. **Aurora レプリカラグアラーム**
   - メトリクス: Aurora AuroraReplicaLag
   - 閾値: 1秒以上のラグ
   - アクション: critical-alerts SNSトピックへ通知

#### ALB関連アラーム
1. **ALB 5xxエラー率アラーム**
   - メトリクス: ALB HTTPCode_Target_5XX_Count
   - 閾値: 5分間でエラー率5%以上
   - アクション: critical-alerts SNSトピックへ通知

2. **ALB ターゲットヘルスチェック失敗アラーム**
   - メトリクス: ALB UnHealthyHostCount
   - 閾値: 1以上のUnhealthyホスト
   - アクション: critical-alerts SNSトピックへ通知

3. **ALB レスポンスタイムアラーム**
   - メトリクス: ALB TargetResponseTime
   - 閾値: 平均4秒以上が5分間継続
   - アクション: warning-alerts SNSトピックへ通知

### 6.4 Amazon SNSトピックの作成

#### critical-alerts トピック
- 用途: クリティカルなアラート通知
- サブスクリプション: メール（設定値から取得）
- オプション: Slack通知（Lambda統合、将来実装）

#### warning-alerts トピック
- 用途: 警告レベルのアラート通知
- サブスクリプション: メール（設定値から取得）

### 6.5 CloudWatch Dashboardの作成

#### ダッシュボード名
- `{envName}-application-dashboard`

#### ダッシュボードウィジェット

##### ECS メトリクス
- ECS CPU使用率（サービス単位）
- ECS メモリ使用率（サービス単位）
- ECS タスク数（実行中/希望数）
- エラーログ数（メトリクスフィルタから）

##### Aurora メトリクス
- Aurora CPU使用率（プライマリ/レプリカ）
- Aurora 接続数
- Aurora レプリカラグ
- Aurora ディスク使用可能量

##### ALB メトリクス
- ALB リクエスト数
- ALB レイテンシ（平均/P50/P95/P99）
- ALB エラー率（4xx/5xx）
- ALB ターゲット健全性

##### VPCエンドポイント メトリクス
- VPCエンドポイント データ転送量
- VPCエンドポイント パケット数

## 依存関係（スタック間参照）

MonitoringStackは以下のスタックからの情報をインポートして使用する。

| スタック | インポートする情報 | 用途 |
|---------|------------------|------|
| ComputeStack | ECSクラスター名、サービス名 | ECSアラーム |
| ComputeStack | ALB ARN | ALBアラーム、ダッシュボード |
| ComputeStack | エラーロググループ名 | メトリクスフィルタ |
| DatabaseStack | Auroraクラスター識別子 | Auroraアラーム、ダッシュボード |

## 受け入れ条件
1. SNSトピック（critical-alerts、warning-alerts）が作成されている
2. CloudWatch Alarmsが作成され、適切なSNSトピックに通知設定されている
3. CloudWatch Dashboardが作成され、すべてのメトリクスが表示されている
4. `cdk synth`が正常に完了する
5. TypeScriptのコンパイルエラーがない

## 制約事項
- SNSメールサブスクリプションは手動確認が必要（サブスクリプション確認メール）
- アラームの閾値は環境設定ファイル（env-config.ts）で調整可能にする
- Auroraのメトリクスはクラスター識別子が必要（DatabaseStackからエクスポート済み）

## 将来対応（スコープ外）
1. Slack通知の実装（Lambda + SNS統合）
2. Amazon Athena設定（S3ログのクエリと分析）
3. X-Rayによる分散トレーシング
4. カスタムメトリクスの追加

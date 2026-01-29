# 要求定義: OrchestrationStack実装

## 概要
AWS CDKを使用して、EventBridgeとStep Functionsによるワークフロー制御基盤（OrchestrationStack）を構築します。これはフェーズ8（8.2 EventBridgeルールの作成、8.3 Step Functionsステートマシンの作成）に該当する、将来的な拡張を見据えたオプション機能の実装です。

基本的なユースケースとして、ECSタスクのスケジュール実行を想定したサンプル実装を提供します。

## 背景
`docs/architecture/implements_aws_by_cdk_plan.md`のフェーズ8では、以下のコンポーネントが「低優先度（後回し）」として定義されていますが、将来的な機能拡張に備えて基盤を整備します。

- **Step Functionsステートマシン**: ワークフローの制御
- **EventBridgeルール**: スケジュールベースまたはイベントベースのトリガー

## 受け入れ条件
- [ ] `cdk/lib/stacks/orchestration-stack.ts`が作成されている
- [ ] Step Functionsステートマシンがデプロイされ、サンプルワークフローが実行可能である
- [ ] EventBridgeルールがデプロイされ、ステートマシンをトリガーできる
- [ ] ECSタスク起動の統合が正しく動作する（既存タスク定義をcontainerOverridesで再利用）
- [ ] サンプルPythonバッチスクリプトが作成されている（DB参照・登録処理）
- [ ] エラーハンドリングとリトライ設定が実装されている
- [ ] CloudWatch Logsへのログ出力が設定されている
- [ ] `cdk/bin/app.ts`にOrchestrationStackが追加されている
- [ ] 環境設定（dev/prod）でオーケストレーション関連のパラメータが定義されている
- [ ] 既存スタック（NetworkStack, DatabaseStack, EcrStack, ComputeStack, MonitoringStack）との依存関係が正しく設定されている
- [ ] CDKデプロイが成功し、リソースが正常に作成される

## 実装対象コンポーネント

### 1. Step Functionsステートマシン
**目的**: ワークフローの制御

**要求内容**:
- サンプルワークフローの定義（ECSタスク起動）
- ECSタスク起動の統合（RunTask API使用）
- エラーハンドリング設定
  - タスク起動失敗時のリトライ（最大3回、指数バックオフ）
  - エラー時の通知（SNSトピック連携、MonitoringStackで作成済み）
- CloudWatch Logsへのログ出力
  - すべての実行ログを記録
  - ログレベル: ALL
- IAMロール設定
  - ECSタスク起動権限（ecs:RunTask）
  - CloudWatch Logs書き込み権限
  - SNS Publish権限（エラー通知用）

### 2. EventBridgeルール
**目的**: スケジュールベースまたはイベントベースのトリガー

**要求内容**:
- スケジュールルールの作成
  - デフォルト: 毎日午前2時（JST）にサンプルワークフロー実行
  - cron式: `cron(0 17 * * ? *)` （UTC、JSTの午前2時）
- ターゲット設定
  - Step Functionsステートマシンへのトリガー
  - 入力変換（必要に応じて）
- IAMロール設定
  - Step Functions実行権限（states:StartExecution）

### 3. Pythonバッチ処理の実行
**目的**: DBアクセスを伴うバッチ処理の実行基盤

**要求内容**:
- 既存のAPI用タスク定義を再利用（containerOverridesでコマンドを上書き）
  - Step FunctionsのECS統合で`ContainerOverrides.Command`を指定
  - 新しいタスク定義は作成しない（シンプルさ優先）
  - DB接続情報、シークレット、VPC設定は既存タスク定義から継承
- サンプルPythonバッチスクリプトの作成
  - `backend/batch/sample_batch.py`
  - DB接続処理（既存の接続設定を使用）
  - データ参照（SELECT）とデータ登録（INSERT/UPDATE）のサンプル実装
  - 適切なログ出力（標準出力）
- 既存のタスク実行ロール・タスクロールをそのまま使用
  - Secrets Manager読み取り権限（既存）
  - CloudWatch Logs書き込み権限（既存）

**将来的な拡張**:
- バッチ処理が重くなり専用リソースが必要な場合は、バッチ専用タスク定義を追加

### 4. 環境設定の拡張
**要求内容**:
- `cdk/lib/config/env-config.ts`に`orchestration`設定を追加
  - スケジュール実行の有効/無効フラグ
  - スケジュール式（cron）
  - ECSタスク設定（クラスター名、タスク定義ARN、サブネット等）
- 開発環境と本番環境で異なる設定を適用可能にする

### 5. CDKアプリケーションの更新
**要求内容**:
- `cdk/bin/app.ts`にOrchestrationStackインスタンスを追加
- 依存関係の設定
  - ComputeStack（ECSクラスター、タスク定義）
  - MonitoringStack（SNSトピック）

## 制約事項

### 技術的制約
- AWS CDK v2を使用
- TypeScriptで実装
- 既存のスタック構造（NetworkStack, DatabaseStack, EcrStack, ComputeStack, MonitoringStack）を参照する形で実装
- Step Functionsの料金を考慮し、開発環境ではスケジュール実行を無効化できるようにする
- EventBridgeルールは開発環境では無効化（enabled: false）し、手動テスト時のみ有効化する

### 依存関係
- **ComputeStack**: ECSクラスター、タスク定義が必要
- **MonitoringStack**: SNSトピック（エラー通知用）が必要
- **NetworkStack**: VPCサブネット情報が必要

### セキュリティ制約
- IAMロールは最小権限の原則に従う
- Step FunctionsからECSタスク起動時は、既存のタスク実行ロールを使用
- CloudWatch Logsのログ保持期間は環境設定に従う

### コスト制約
- Step Functions実行回数を最小限に抑える
- CloudWatch Logsのログ保持期間は環境設定に従い、コストを最適化
- 開発環境ではスケジュール実行を無効化し、不要なコストを削減

## 非機能要件

### 可用性
- ステートマシン実行失敗時のリトライ機能
- エラー時のSNS通知

### 監視
- CloudWatch Logsへのすべての実行ログ記録
- ステートマシン実行メトリクスのCloudWatch送信

### 拡張性
- 将来的に他のワークフロー（データバックアップ、レポート生成等）を追加しやすい設計
- ステートマシン定義を外部ファイル化できる構造

## 参照ドキュメント
- `docs/architecture/implements_aws_by_cdk_plan.md` - フェーズ8（8.2, 8.3）
- 既存スタック実装
  - `cdk/lib/stacks/compute-stack.ts` - ECS関連リソース
  - `cdk/lib/stacks/monitoring-stack.ts` - SNSトピック
  - `cdk/lib/stacks/network-stack.ts` - VPC情報
- `cdk/lib/config/env-config.ts` - 環境設定インターフェース

## 除外事項
以下は本フェーズの対象外とします。
- AWS Amplifyの構築（フェーズ8.4、別途実装）
- Amazon Athenaの設定（フェーズ8.1、別途実装）
- 複雑なワークフロー（現時点ではサンプル実装のみ）
- Step Functions Expressワークフロー（標準ワークフローのみ実装）

## 補足事項

### サンプルワークフローの内容
最小限の実装として、以下のワークフローを実装します。
1. ECSタスクの起動（Pythonバッチ処理タスク）
2. タスク完了待機
3. 成功/失敗の判定
4. エラー時のSNS通知

### Pythonバッチ処理タスクの内容
サンプルとして、データベースにアクセスするPythonバッチ処理を実装します。
- **実行ファイル**: 通常のPythonスクリプト（FastAPIエンドポイントではない）
- **処理内容**:
  - Aurora PostgreSQLへの接続
  - データの参照（SELECT）
  - データの登録（INSERT/UPDATE）
- **想定ユースケース**: 定期的なデータ集計、レポート用データ作成、マスタデータ更新など
- **実行環境**: 既存のバックエンドコンテナイメージを使用し、エントリーポイントをバッチスクリプトに変更

### 将来的な拡張想定
- データベースバックアップワークフロー
- レポート生成バッチ
- 定期的なデータクリーンアップ
- 外部APIとの連携処理

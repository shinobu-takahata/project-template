# 設計書: FireLensとFluent Bitを使用したログルーティング機能の実装

## 実装アプローチ

### アーキテクチャ概要
ECS Fargateタスク内に、アプリケーションコンテナ（FastAPI）とログルーターコンテナ（Fluent Bit）をサイドカーパターンで配置します。アプリケーションコンテナはFireLensログドライバーを使用してFluent Bitにログを転送し、Fluent Bitがログレベルに応じて適切な送信先（CloudWatch LogsまたはS3）にルーティングします。

```
┌─────────────────────────────────────────────┐
│         ECS Fargate Task                     │
│                                              │
│  ┌──────────────────┐                       │
│  │  FastAPI         │                       │
│  │  Container       │                       │
│  │  (Port 8000)     │                       │
│  └─────────┬────────┘                       │
│            │ FluentD Forward                │
│            │ Protocol (24224)               │
│            ↓                                 │
│  ┌──────────────────┐                       │
│  │  Fluent Bit      │                       │
│  │  Log Router      │                       │
│  │  (FireLens)      │                       │
│  └─────────┬────────┘                       │
│            │                                 │
│         ┌──┴──┐                             │
│         ↓     ↓                             │
│    ERROR+  全ログ                           │
└─────┼──────┼─────────────────────────────┘
      │      │
      │      └──────────────────┐
      ↓                         ↓
┌──────────────────┐   ┌──────────────────┐
│ CloudWatch Logs  │   │  S3 Bucket       │
│ /ecs/backend/    │   │  (Compressed)    │
│ errors           │   │  Long-term       │
└──────────────────┘   └──────────────────┘
```

### カスタムFluent Bitイメージ方式を採用する理由
1. **設定のバージョン管理**: Dockerfileと設定ファイルをGitで管理可能
2. **デプロイの確実性**: イメージに設定が含まれるため、外部依存なし
3. **環境変数での動的設定**: ログバケット名やリージョンを環境変数で切り替え可能
4. **テストの容易性**: ローカルでイメージをビルドしてテスト可能

## 変更対象コンポーネント

### 1. 新規作成ファイル
#### Fluent Bit設定ファイル
- **ディレクトリ**: `cdk/docker/fluent-bit/`
- **ファイル**:
  - `Dockerfile`: カスタムFluent Bitイメージ定義
  - `fluent-bit.conf`: メイン設定ファイル（入力、フィルタ、出力設定）
  - `parsers.conf`: ログパーサー定義（JSON形式パース）

### 2. 変更ファイル
#### CDKスタック
- **`cdk/lib/stacks/compute-stack.ts`**:
  - Fluent Bit用ECRリポジトリの作成
  - ECSタスク定義へのFireLensログルーター追加
  - アプリケーションコンテナのログドライバー変更（FireLens経由）
  - タスクロールへのS3書き込み権限とCloudWatch Logs書き込み権限の追加

- **`cdk/lib/stacks/monitoring-stack.ts`**:
  - CloudWatch Logsロググループの作成（既存の場合は参照のみ）
  - S3ログバケットの作成（既存の場合は参照のみ）

## データ構造の変更

### Fluent Bit設定構造
#### INPUT（入力）
```
[INPUT]
    Name        forward
    Listen      0.0.0.0
    Port        24224
```
- アプリケーションコンテナからFluentD Forward Protocolでログを受信

#### FILTER（フィルタ）
```
[FILTER]
    Name        parser
    Match       *
    Key_Name    log
    Parser      json
    Reserve_Data On
```
- JSON形式のログをパース
- `level` フィールドを抽出してログレベル判定に使用

#### OUTPUT 1（CloudWatch Logs - ERRORレベル以上）
```
[OUTPUT]
    Name        cloudwatch_logs
    Match       *
    region      ${AWS_REGION}
    log_group_name    /ecs/backend/errors
    log_stream_prefix fargate-
    auto_create_group true
    log_key     log
    Grep        level ERROR,CRITICAL,FATAL
```
- ERRORレベル以上のログをフィルタリング
- CloudWatch Logsに送信

#### OUTPUT 2（S3 - 全ログ）
```
[OUTPUT]
    Name        s3
    Match       *
    region      ${AWS_REGION}
    bucket      ${LOG_BUCKET_NAME}
    total_file_size  100M
    upload_timeout   10m
    s3_key_format    /logs/year=%Y/month=%m/day=%d/hour=%H/%H%M%S-$UUID.gz
    compression      gzip
    store_dir        /tmp/fluent-bit/s3
```
- 全ログをS3にアップロード
- 100MB単位でファイルローテーション
- gzip圧縮
- 時間別パーティショニング

### ECSタスク定義の変更
```typescript
// Before (AwsLogDriver)
logging: ecs.LogDrivers.awsLogs({
  streamPrefix: 'backend',
  logGroup: new logs.LogGroup(this, 'BackendLogGroup', {
    logGroupName: '/ecs/backend',
    retention: logs.RetentionDays.ONE_WEEK
  })
})

// After (FireLens)
logging: ecs.LogDrivers.firelens({
  options: {
    Name: 'forward',
    Host: 'log-router',
    Port: '24224',
    'Retry_Limit': '2'
  }
})
```

### 環境変数
Fluent Bitコンテナに以下の環境変数を渡す:
- `AWS_REGION`: ap-northeast-1
- `LOG_BUCKET_NAME`: S3ログバケット名（動的に設定）

## 影響範囲

### 影響を受けるリソース
1. **ECS Fargate Task Definition**
   - サイドカーコンテナ（Fluent Bit）の追加
   - メモリ配分の調整（Fluent Bit用に50MB予約）
   - ログドライバーの変更

2. **IAMロール**
   - タスクロールに新しい権限追加:
     - `s3:PutObject` （ログバケットへ）
     - `logs:CreateLogGroup`、`logs:CreateLogStream`、`logs:PutLogEvents` （CloudWatch Logsへ）
   - タスク実行ロールに新しい権限追加:
     - `ecr:GetAuthorizationToken`、`ecr:BatchCheckLayerAvailability`、`ecr:GetDownloadUrlForLayer`、`ecr:BatchGetImage` （Fluent Bit ECRイメージプル用）

3. **ECRリポジトリ**
   - 新規リポジトリ: `fluent-bit-custom`
   - ライフサイクルポリシー: 最新5イメージを保持

4. **CloudWatch Logs**
   - 新規ロググループ: `/ecs/firelens` （Fluent Bit自体のログ用）
   - 既存ロググループ: `/ecs/backend/errors` （エラーログ用、既に作成済みの想定）

5. **S3バケット**
   - 既存バケット使用（MonitoringStackで作成）
   - バケットポリシーにタスクロールからのアクセス許可追加

### 影響を受けないリソース
- VPC、サブネット
- ALB、ターゲットグループ
- Aurora Database
- セキュリティグループ（既存のまま）
- Auto Scaling設定

## 技術的決定事項

### 決定1: カスタムFluent Bitイメージ方式を採用
**理由**:
- 設定ファイルをGitで管理でき、バージョン管理が容易
- デプロイ時に外部依存（S3設定ファイル取得など）がない
- ローカルでテストしやすい

**代替案**: S3に設定ファイルを配置してECS起動時にダウンロード
- 却下理由: 外部依存が増え、デプロイが複雑化

### 決定2: CloudWatch Logsへの送信にGrepフィルタを使用
**理由**:
- Fluent Bitの標準機能でログレベルフィルタリングが可能
- 設定がシンプル
- ERRORレベル以上（ERROR、CRITICAL、FATAL）を簡単に指定可能

**代替案**: Luaスクリプトでフィルタリング
- 却下理由: 設定が複雑化し、メンテナンスコストが上がる

### 決定3: S3ログファイルのパーティショニング形式
**パーティショニング形式**: `/logs/year=%Y/month=%m/day=%d/hour=%H/`
**理由**:
- Athenaでパーティションクエリが効率的
- 日時ベースのログ検索が高速
- ログ削除やアーカイブの管理が容易

### 決定4: ログファイルサイズとローテーション
**設定**: 100MB単位でローテーション、10分タイムアウト
**理由**:
- ログの即時性とファイルサイズのバランス
- S3 API呼び出し回数の最適化（コスト削減）
- メモリ使用量の抑制

## セキュリティ考慮事項

### IAM権限の最小化
- タスクロールにはログバケットへの `s3:PutObject` のみ付与（読み取り権限は不要）
- CloudWatch Logsへの書き込み権限は `/ecs/backend/errors` ロググループに限定

### ログの暗号化
- S3ログバケット: SSE-S3による暗号化
- CloudWatch Logs: デフォルトで暗号化

### ネットワークセキュリティ
- Fluent BitコンテナはプライベートサブネットのECSタスク内で動作
- CloudWatch LogsとS3へのアクセスはVPCエンドポイント経由（NAT Gatewayを使用しない）

## コスト影響

### CloudWatch Logsコスト削減
- **Before**: 全ログをCloudWatch Logsに送信（月間100GB想定）
  - データ取り込み: 100GB × $0.50/GB = $50
  - ストレージ: 100GB × $0.03/GB = $3
  - 合計: 約$53/月

- **After**: ERRORログのみCloudWatch Logsに送信（月間10GB想定）
  - データ取り込み: 10GB × $0.50/GB = $5
  - ストレージ: 10GB × $0.03/GB = $0.3
  - 合計: 約$5.3/月
  - **削減額**: 約$47.7/月（約90%削減）

### S3ストレージコスト
- 全ログをS3に保存（月間100GB、gzip圧縮で約30GB想定）
  - Standard: 30GB × $0.025/GB = $0.75/月
  - 90日後Glacier移行: 約$0.004/GB = 約$0.12/月
- **合計**: 約$0.87/月（CloudWatch Logsの約1/6）

### 追加コスト
- Fluent Bit ECRストレージ: 約$0.10/月（イメージサイズ約1GB、5イメージ保持）
- Fluent Bitメモリ使用: 50MB × タスク数（Fargateメモリ料金に含まれる、増加分は約$0.5/月）

### 総コスト削減効果
- **削減額**: 約$47/月（年間約$564）

## パフォーマンス考慮事項

### Fluent Bitのリソース配分
- メモリ予約: 50MB
- CPUシェア: 未指定（ベストエフォート）

### ログバッファリング
- S3アップロード: `/tmp/fluent-bit/s3` ディレクトリでバッファリング
- メモリ使用量を抑えるため、ファイルシステムベースのバッファリングを使用

### ヘルスチェック
- エンドポイント: `http://localhost:2020/api/v1/health`
- 間隔: 30秒
- タイムアウト: 3秒

## テスト計画

### 単体テスト
1. **Fluent Bitイメージのビルド**
   - Dockerfileの構文チェック
   - 設定ファイルの構文チェック（`fluent-bit -c fluent-bit.conf --dry-run`）

2. **ローカルテスト**
   - docker-composeでFluent Bitコンテナを起動
   - テストログを送信してフィルタリング動作を確認

### 統合テスト
1. **ECSタスク起動テスト**
   - CDKデプロイ後、ECSタスクが正常に起動するか確認
   - Fluent Bitコンテナのヘルスチェックが成功するか確認

2. **ログルーティングテスト**
   - FastAPIアプリからINFOログを出力
     - S3にログが保存されることを確認
     - CloudWatch Logsに送信されないことを確認
   - FastAPIアプリからERRORログを出力
     - S3とCloudWatch Logs両方にログが保存されることを確認

3. **パーティショニングテスト**
   - S3バケットでログファイルパスが `logs/year=YYYY/month=MM/day=DD/hour=HH/` の形式になっていることを確認

### パフォーマンステスト
1. **高負荷時のログ送信**
   - 大量のログを短時間で出力
   - Fluent Bitがログを正常に処理できるか確認
   - メモリ使用量が許容範囲内か確認

2. **ログ遅延テスト**
   - ログ出力からS3/CloudWatch Logsへの送信までの遅延を測定
   - 許容範囲（数秒以内）に収まるか確認

## ロールバック計画

### ロールバック手順
1. ECSタスク定義を前のバージョンにロールバック
2. ECSサービスを更新して前のタスク定義を使用
3. Fluent Bit ECRイメージを削除（オプション）

### ロールバック時の影響
- ログが再びCloudWatch Logsに直接送信される
- S3へのログ保存が停止する
- CloudWatch Logsのコストが増加する

### ロールバックトリガー
- ECSタスクが起動しない
- Fluent Bitコンテナのヘルスチェックが失敗し続ける
- ログが正常にCloudWatch LogsまたはS3に送信されない
- アプリケーションのパフォーマンスが著しく低下する

## 運用考慮事項

### モニタリング
1. **Fluent Bitコンテナのログ監視**
   - CloudWatch Logs `/ecs/firelens` でFluent Bitのエラーログを確認

2. **CloudWatch Metrics**
   - ECSタスクのメモリ使用量を監視（Fluent Bit追加による増加を確認）

3. **S3ログファイル監視**
   - S3バケットのオブジェクト数とサイズを定期的に確認
   - ライフサイクルポリシーが正常に動作しているか確認

### トラブルシューティング
- **ログがCloudWatch Logsに送信されない**: Fluent Bit設定ファイルのGrepフィルタを確認、タスクロールの権限を確認
- **ログがS3に送信されない**: タスクロールのS3書き込み権限を確認、バケットポリシーを確認
- **Fluent Bitコンテナが起動しない**: ECRイメージが存在するか確認、タスク実行ロールの権限を確認

## 参照実装

### ディレクトリ構造
```
cdk/
├── docker/
│   └── fluent-bit/
│       ├── Dockerfile
│       ├── fluent-bit.conf
│       └── parsers.conf
└── lib/
    └── stacks/
        ├── compute-stack.ts  (変更)
        └── monitoring-stack.ts  (変更)
```

## 次のステップ
1. Fluent Bit設定ファイルの作成
2. カスタムFluent BitイメージのビルドとECRプッシュ
3. CDKコードの変更とデプロイ
4. ログルーティングの動作確認
5. CloudWatch Alarmsの設定（エラーログ検出）

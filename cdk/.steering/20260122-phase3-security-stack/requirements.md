# フェーズ3: セキュリティ基盤 - 要求事項

## 概要
GuardDuty、AWS Config、WAFを構築し、セキュリティ基盤を強化します。脅威検出、リソース構成監査、Webアプリケーション保護を実現します。

## 目的
- GuardDutyで脅威検出サービスを有効化する
- AWS Configでリソース構成の記録と監査を実現する
- WAF Web ACLでWebアプリケーションを保護する（ALB用）
- セキュリティイベントの監視基盤を構築する

## スコープ

### 含まれるもの
1. **GuardDuty Detectorの有効化**
   - 脅威検出サービスの有効化
   - データソースの設定（VPCフローログ、DNS、CloudTrail、S3）
   - 環境ごとの設定

2. **AWS Configの設定**
   - Config Recorderの作成
   - 記録対象リソースの設定（全リソース）
   - S3バケット（Config記録用）の作成
   - Delivery Channelの設定
   - IAMロールの作成

3. **WAF Web ACLの作成**
   - ALB用のWeb ACL作成（リージョナル）
   - マネージドルールセットの適用
     - AWSManagedRulesCommonRuleSet
     - AWSManagedRulesKnownBadInputsRuleSet
     - AWSManagedRulesSQLiRuleSet
   - CloudWatch Metricsの有効化

4. **削除ポリシー設定**
   - 環境ごとの削除ポリシー定義
   - 開発環境: Config S3バケットは削除可能
   - 本番環境: Config S3バケットは保持

### 含まれないもの
- ALBへのWAF関連付け（フェーズ5で実施）
- GuardDutyの検出結果通知（フェーズ6で実施）
- AWS Configルールの設定（オプション機能）
- セキュリティハブの統合（オプション機能）

## 機能要件

### FR-1: GuardDuty Detector
- **FR-1.1**: GuardDuty Detectorを有効化
- **FR-1.2**: データソースを設定
  - VPCフローログ: 有効
  - DNSログ: 有効
  - CloudTrailイベント: 有効
  - S3ログ: 有効
- **FR-1.3**: ap-northeast-1リージョンで有効化
- **FR-1.4**: 環境ごとの設定（dev/prod）

### FR-2: AWS Config
- **FR-2.1**: Config Recorderを作成
  - 記録対象: すべてのリソース
  - グローバルリソース: 有効
- **FR-2.2**: S3バケット（Config記録用）を作成
  - バケット名: `config-{envName}-{accountId}`
  - 暗号化: S3マネージド暗号化
  - バージョニング: 有効
  - パブリックアクセス: ブロック
  - 削除ポリシー: 環境設定に従う
- **FR-2.3**: Delivery Channelを設定
  - 配信先: S3バケット
  - 配信頻度: 定期的
- **FR-2.4**: IAMロールを作成
  - Config Recorderが使用するロール
  - 必要な権限: AWS Configサービスロールポリシー

### FR-3: WAF Web ACL
- **FR-3.1**: Web ACLを作成（リージョナル）
  - スコープ: REGIONAL（ALB用）
  - デフォルトアクション: Allow
  - CloudWatch Metrics: 有効
- **FR-3.2**: マネージドルールセットを追加
  - **ルール1**: AWSManagedRulesCommonRuleSet（優先度: 1）
  - **ルール2**: AWSManagedRulesKnownBadInputsRuleSet（優先度: 2）
  - **ルール3**: AWSManagedRulesSQLiRuleSet（優先度: 3）
- **FR-3.3**: 各ルールの設定
  - OverrideAction: None
  - VisibilityConfig: サンプリング有効、メトリクス有効
- **FR-3.4**: Web ACL ARNをエクスポート（フェーズ5で使用）

## 非機能要件

### NFR-1: セキュリティ
- GuardDutyで脅威を継続的に検出
- AWS Configで構成変更を記録・監査
- WAFでWebアプリケーションを保護

### NFR-2: コンプライアンス
- AWS Configでコンプライアンス監査をサポート
- 構成変更履歴を保持

### NFR-3: コスト最適化
- GuardDuty: 使用量ベースの課金（約$10-30/月）
- AWS Config: 記録項目数ベースの課金（約$10-20/月）
- WAF: Web ACLとルール数ベースの課金（約$5-10/月）

### NFR-4: 保守性
- 環境設定から動的にリソースを作成
- 削除ポリシーで環境ごとの削除動作を制御
- 明確なリソース命名規則

### NFR-5: 拡張性
- 将来的なWAFルール追加に対応可能
- AWS Configルールの追加が容易

## 制約事項

### C-1: リージョン
- ap-northeast-1（東京リージョン）固定

### C-2: GuardDuty
- リージョンごとに有効化が必要
- マルチリージョン展開は対象外

### C-3: AWS Config
- S3バケットは同一リージョンに作成
- Config Recorderは1リージョンにつき1つ

### C-4: WAF
- Web ACLはリージョナル（ALB用）
- CloudFront用WAFは対象外

## 受け入れ条件

### AC-1: GuardDuty
- [ ] GuardDuty Detectorが有効化されている
- [ ] すべてのデータソースが有効化されている
- [ ] ap-northeast-1リージョンで動作している

### AC-2: AWS Config
- [ ] Config Recorderが作成されている
- [ ] すべてのリソースが記録対象になっている
- [ ] S3バケットが作成されている
- [ ] Delivery Channelが設定されている
- [ ] IAMロールが適切に設定されている
- [ ] 削除ポリシーが環境設定に従っている

### AC-3: WAF Web ACL
- [ ] Web ACLが作成されている（リージョナル）
- [ ] 3つのマネージドルールセットが設定されている
- [ ] CloudWatch Metricsが有効化されている
- [ ] Web ACL ARNがエクスポートされている

### AC-4: ビルドとデプロイ
- [ ] TypeScriptのコンパイルが正常に完了する
- [ ] `cdk synth --context env=dev`が正常に完了する
- [ ] `cdk synth --context env=prod`が正常に完了する
- [ ] CloudFormationテンプレートが生成される
- [ ] （オプション）`cdk deploy SecurityStack-dev`が正常に完了する

## 依存関係

### 前提条件
- フェーズ1（基盤セットアップ）が完了していること
- フェーズ2（ネットワーク基盤）が完了していること（VPCフローログ用）
- 環境設定ファイル（env-config.ts、dev.ts、prod.ts）が存在すること

### 後続フェーズへの影響
- フェーズ5（ComputeStack）: WAF Web ACLをALBに関連付け
- フェーズ6（MonitoringStack）: GuardDuty検出結果をSNSで通知

## リスクと対策

### R-1: GuardDutyのコスト
- **リスク**: データ量が多いとコストが増加する可能性
- **対策**: 初期は最小限のデータソースで開始し、必要に応じて追加

### R-2: AWS Configの記録コスト
- **リスク**: 記録項目数が多いとコストが増加
- **対策**: 記録対象を全リソースとするが、不要なリソースタイプは後で除外可能

### R-3: WAFのルール設定
- **リスク**: ルールが厳しすぎると正常なリクエストがブロックされる可能性
- **対策**:
  - デフォルトアクションをAllowに設定
  - マネージドルールセットを使用し、実績のあるルールを適用
  - 必要に応じてルールをカスタマイズ

### R-4: Config S3バケットの削除
- **リスク**: 本番環境で誤ってバケットを削除すると監査証跡が失われる
- **対策**:
  - 本番環境の削除ポリシーをRETAINに設定
  - バケットバージョニングを有効化

## 参考資料
- [AWS GuardDuty公式ドキュメント](https://docs.aws.amazon.com/guardduty/)
- [AWS Config公式ドキュメント](https://docs.aws.amazon.com/config/)
- [AWS WAF公式ドキュメント](https://docs.aws.amazon.com/waf/)
- [implements_aws_by_cdk_plan.md](../../docs/architecture/implements_aws_by_cdk_plan.md) - フェーズ3セクション

# フェーズ2: ネットワーク基盤 - 要求事項

## 概要
マルチAZ構成のVPC、VPCエンドポイント、Route 53を構築します。NAT Gatewayの代わりにVPCエンドポイントを使用してコストを最適化します。

## 目的
- マルチAZ構成のVPCを作成する
- NAT Gatewayの代わりにVPCエンドポイントを使用してコストを削減する（年間約$420削減）
- Route 53でカスタムドメインを管理する準備を整える
- 後続フェーズでのリソース配置の基盤を構築する

## スコープ

### 含まれるもの
1. **VPC作成**
   - マルチAZ構成（ap-northeast-1a、ap-northeast-1c）
   - パブリックサブネット × 2
   - プライベートサブネット × 2（Isolated Subnet）
   - インターネットゲートウェイ
   - ルートテーブル設定
   - VPCフローログ（CloudWatch Logs）

2. **VPCエンドポイント**
   - Gateway型: S3（無料）
   - Interface型: ECR API、ECR DKR、Secrets Manager、CloudWatch Logs（有料）
   - セキュリティグループ設定

3. **Route 53**
   - Hosted Zoneの参照（既存の場合）
   - 新規作成のオプションサポート

4. **削除ポリシー設定**
   - 環境ごとの削除ポリシー定義
   - 開発環境: 完全削除可能
   - 本番環境: データ保護

### 含まれないもの
- ACM証明書の作成（フェーズ5で実装）
- ALB用のAレコード（フェーズ5で実装）
- セキュリティ関連リソース（GuardDuty、Config、WAF - フェーズ3）
- データベース（Aurora - フェーズ4）
- コンピューティングリソース（ECS、ALB - フェーズ5）

## 機能要件

### FR-1: VPC作成
- **FR-1.1**: 環境設定から取得したCIDRでVPCを作成
  - 開発環境: 10.0.0.0/16
  - 本番環境: 10.1.0.0/16
- **FR-1.2**: 2つのAvailability Zoneを使用（ap-northeast-1a、ap-northeast-1c）
- **FR-1.3**: パブリックサブネット × 2を作成
  - 開発環境: 10.0.1.0/24、10.0.2.0/24
  - 本番環境: 10.1.1.0/24、10.1.2.0/24
- **FR-1.4**: プライベートサブネット × 2を作成（PRIVATE_ISOLATED）
  - 開発環境: 10.0.11.0/24、10.0.12.0/24
  - 本番環境: 10.1.11.0/24、10.1.12.0/24
- **FR-1.5**: インターネットゲートウェイをパブリックサブネットに関連付け
- **FR-1.6**: NAT Gatewayは作成しない（コスト最適化）
- **FR-1.7**: VPCフローログをCloudWatch Logsに出力
- **FR-1.8**: 適切なタグ付け
  - Environment: dev/prod
  - Project: project-template
  - ManagedBy: CDK

### FR-2: VPCエンドポイント作成

#### FR-2.1: Gateway型エンドポイント（S3）
- **FR-2.1.1**: S3用のGatewayエンドポイントを作成
- **FR-2.1.2**: プライベートサブネットのルートテーブルに自動追加
- **FR-2.1.3**: コスト: $0（無料）

#### FR-2.2: Interface型エンドポイント
- **FR-2.2.1**: ECR API用のInterfaceエンドポイントを作成
- **FR-2.2.2**: ECR DKR用のInterfaceエンドポイントを作成
- **FR-2.2.3**: Secrets Manager用のInterfaceエンドポイントを作成
- **FR-2.2.4**: CloudWatch Logs用のInterfaceエンドポイントを作成
- **FR-2.2.5**: プライベートサブネットに配置（マルチAZ）
- **FR-2.2.6**: Private DNSを有効化
- **FR-2.2.7**: セキュリティグループの作成
  - インバウンド: VPC CIDR範囲からのHTTPS (443)
  - アウトバウンド: 制限なし（デフォルト）
- **FR-2.2.8**: コスト: 約$7.2/月/個 × 4個 = 約$28.8/月

#### FR-2.3: 環境別のVPCエンドポイント制御
- **FR-2.3.1**: `useVpcEndpoints`フラグで有効/無効を切り替え可能
- **FR-2.3.2**: 開発・本番環境ともにデフォルトで有効

### FR-3: Route 53 Hosted Zone
- **FR-3.1**: 既存のHosted Zoneを参照（fromLookup）
- **FR-3.2**: 新規作成のオプションをサポート（コメントアウト）
- **FR-3.3**: ドメイン名は環境設定から取得
  - 開発環境: dev-api.example.com
  - 本番環境: api.example.com

### FR-4: 削除ポリシー
- **FR-4.1**: EnvConfigに削除ポリシー設定を追加
  - s3Buckets: 'RETAIN' | 'DESTROY'
  - logGroups: 'RETAIN' | 'DESTROY'
  - database: 'RETAIN' | 'SNAPSHOT' | 'DESTROY'
- **FR-4.2**: 開発環境はすべて'DESTROY'（完全削除可能）
- **FR-4.3**: 本番環境はすべて'RETAIN'または'SNAPSHOT'（データ保護）
- **FR-4.4**: VPCフローログのロググループに削除ポリシーを適用

## 非機能要件

### NFR-1: コスト最適化
- NAT Gateway（約$64/月）の代わりにVPCエンドポイント（約$28.8/月）を使用
- 年間約$420のコスト削減

### NFR-2: 高可用性
- マルチAZ構成（2つのAZ）
- VPCエンドポイントもマルチAZ配置

### NFR-3: セキュリティ
- プライベートサブネットは完全分離（PRIVATE_ISOLATED）
- VPCエンドポイント用のセキュリティグループは最小権限
- VPCフローログで通信を監査

### NFR-4: 保守性
- 環境設定から動的にリソースを作成
- 削除ポリシーで環境ごとの削除動作を制御
- 明確なリソース命名規則

### NFR-5: 拡張性
- 将来的なサブネット追加に対応可能な構造
- VPCエンドポイントの追加が容易

## 制約事項

### C-1: リージョン
- ap-northeast-1（東京リージョン）固定

### C-2: Availability Zone
- ap-northeast-1a、ap-northeast-1c の2つのAZ固定

### C-3: Route 53
- ドメインは事前に取得済みであること
- Hosted Zoneが存在する場合はfromLookupを使用
- 存在しない場合は手動作成が必要

### C-4: VPCエンドポイント
- Interface型エンドポイントは有料（約$7.2/月/個）
- コストを考慮して必要最小限に制限

## 受け入れ条件

### AC-1: VPC作成
- [ ] VPCが環境設定のCIDRで作成されている
- [ ] パブリックサブネット × 2が作成されている
- [ ] プライベートサブネット × 2が作成されている（PRIVATE_ISOLATED）
- [ ] インターネットゲートウェイが作成されている
- [ ] NAT Gatewayが作成されていないこと
- [ ] VPCフローログがCloudWatch Logsに出力されている
- [ ] 適切なタグが付与されている

### AC-2: VPCエンドポイント
- [ ] S3用のGatewayエンドポイントが作成されている
- [ ] ECR API用のInterfaceエンドポイントが作成されている
- [ ] ECR DKR用のInterfaceエンドポイントが作成されている
- [ ] Secrets Manager用のInterfaceエンドポイントが作成されている
- [ ] CloudWatch Logs用のInterfaceエンドポイントが作成されている
- [ ] VPCエンドポイント用のセキュリティグループが作成されている
- [ ] Private DNSが有効化されている

### AC-3: Route 53
- [ ] Hosted Zoneが参照されている（または作成されている）
- [ ] NetworkStackからHosted Zoneがエクスポートされている

### AC-4: 削除ポリシー
- [ ] EnvConfigに削除ポリシー設定が追加されている
- [ ] 開発環境はDESTROYに設定されている
- [ ] 本番環境はRETAINに設定されている
- [ ] VPCフローログのロググループに削除ポリシーが適用されている

### AC-5: ビルドとデプロイ
- [ ] TypeScriptのコンパイルが正常に完了する
- [ ] `cdk synth --context env=dev`が正常に完了する
- [ ] `cdk synth --context env=prod`が正常に完了する
- [ ] CloudFormationテンプレートが生成される
- [ ] （オプション）`cdk deploy NetworkStack-dev`が正常に完了する

## 依存関係

### 前提条件
- フェーズ1（基盤セットアップ）が完了していること
- 環境設定ファイル（env-config.ts、dev.ts、prod.ts）が存在すること
- Route 53のHosted Zoneが存在すること（fromLookupを使用する場合）

### 後続フェーズへの影響
- フェーズ3（SecurityStack）: VPCを参照
- フェーズ4（DatabaseStack）: VPCとプライベートサブネットを参照
- フェーズ5（ComputeStack）: VPC、サブネット、Hosted Zoneを参照
- フェーズ6（MonitoringStack）: VPCを参照

## リスクと対策

### R-1: VPCエンドポイントのコスト
- **リスク**: Interface型エンドポイント4個で約$28.8/月のコストが発生
- **対策**: NAT Gatewayと比較すると約$35/月削減できるため、コスト面では有利

### R-2: Route 53 Hosted Zoneが存在しない
- **リスク**: fromLookupで参照できずデプロイが失敗する
- **対策**: 
  - 事前にHosted Zoneの存在を確認
  - 存在しない場合は手動作成または新規作成オプションを使用

### R-3: VPCフローログのCloudWatch Logsコスト
- **リスク**: VPCフローログのデータ量が多いとコストが増加
- **対策**: 
  - ログ保持期間を適切に設定（開発: 7日、本番: 30日）
  - 必要に応じてS3への直接出力に変更

### R-4: 削除時のENI残存
- **リスク**: VPCエンドポイントのENI（Elastic Network Interface）が削除に時間がかかる
- **対策**: 
  - 削除時は5-10分待機
  - 手動でENIを削除する方法をドキュメント化

## 参考資料
- [AWS CDK公式ドキュメント - VPC](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_ec2.Vpc.html)
- [VPCエンドポイント](https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints.html)
- [implements_aws_by_cdk_plan.md](../../docs/architecture/implements_aws_by_cdk_plan.md) - フェーズ2セクション

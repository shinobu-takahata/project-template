# AWS コスト見積もり

> 作成日: 2026-03-17
> リージョン: ap-northeast-1 (東京)
> CDK構成を元に算出

## 前提条件・仮定

- Dev / Prod 両環境を常時稼働
- トラフィック: 低〜中程度（月間リクエスト 100万未満）
- DB ストレージ: Dev 20GB / Prod 100GB
- ECS タスク数: Dev 常時2台, Prod 常時2台（最大20台まで Auto Scaling）

---

## Dev 環境 月額見積もり

| サービス | 構成 | 月額 |
|---------|------|------|
| ECS Fargate | 0.5vCPU × 1GB × 2タスク | ~$45 |
| Aurora PostgreSQL | db.t3.medium × 2台（Writer + Reader） | ~$136 |
| ALB | internet-facing × 1 | ~$20 |
| VPC Interface Endpoints | 4種（ECR API/DKR, Secrets Manager, CloudWatch Logs）× 2AZ | ~$82 |
| CloudWatch | ログ7日保持・各種アラーム・Dashboard・Container Insights | ~$30 |
| WAF | WebACL + Managed Rules 3本（Common, KnownBadInputs, SQLi） | ~$10 |
| GuardDuty | 基本検知 | ~$15 |
| AWS Config | allSupported=true（全リソース記録） | ~$15 |
| S3 | ALBログ・アプリログ・Configバケット | ~$5 |
| その他 | Secrets Manager, ECR, SNS | ~$3 |
| **合計** | | **~$361 /月** |

---

## Prod 環境 月額見積もり（通常時 desiredCount=2）

| サービス | 構成 | 月額 |
|---------|------|------|
| ECS Fargate | 1vCPU × 2GB × 2タスク（最大20台までスケール） | ~$90〜$900 |
| Aurora PostgreSQL | db.r6g.large × 2台（Writer + Reader）+ Performance Insights | ~$380 |
| ALB | internet-facing × 1 | ~$20 |
| VPC Interface Endpoints | 4種 × 2AZ | ~$82 |
| CloudWatch | ログ30日保持・各種アラーム・Dashboard・Container Insights | ~$50 |
| WAF | WebACL + Managed Rules 3本 | ~$10 |
| GuardDuty | 基本検知 | ~$20 |
| AWS Config | 全リソース記録 | ~$20 |
| Step Functions | 毎日1回実行（JST 02:00） | ~$1 |
| S3 | ログ・アプリデータ（90日後 Glacier 自動移行） | ~$10 |
| その他 | Secrets Manager, ECR, SNS, EventBridge | ~$5 |
| **合計（通常時）** | | **~$688 /月** |

---

## Dev + Prod 合計

| 環境 | 月額 | 年額 |
|------|------|------|
| Dev | ~$361 | ~$4,332 |
| Prod | ~$688 | ~$8,256 |
| **合計** | **~$1,049** | **~$12,588** |

---

## コスト構造の特性

### 固定費と変動費の割合

見積もりの **8〜9割が固定費**（Aurora・VPC Endpoints・ECS インスタンス稼働時間）。
月間リクエスト数が 100万程度以下の場合、変動費への影響は小さい。

| 変動費項目 | 単価 |
|-----------|------|
| ALB LCU | ~$0.008/LCU/時間（接続数・帯域による） |
| WAF リクエスト処理 | $0.60/100万リクエスト |
| CloudWatch ログ取り込み | $0.76/GB |
| データ転送（外向き） | $0.114/GB |

---

## 主要コスト要因

1. **Aurora が最大のコスト要因**
   Writer + Reader の2台構成が常時稼働。Dev で月$136、Prod で月$380。

2. **VPC Interface Endpoints が固定で高め**
   4種 × 2AZ で月$82。NAT Gateway の代替として採用しているが、コスト差は小さい。

3. **AWS Config（allSupported=true）**
   リソース数が増えるとコストが上昇する。

---

## コスト削減案

| 施策 | 対象 | 削減効果 |
|------|------|---------|
| Dev の夜間・週末停止（ECS + Aurora） | Dev | 最大 60〜70% 削減（~-$215/月） |
| Aurora を Serverless v2 に変更 | Dev | 停止時ほぼ $0。低トラフィック時に有効 |
| VPC Endpoints を S3 Gateway のみに削減 | Dev | ~-$70/月（S3エンドポイントは無料） |

---

## 備考

- 本見積もりは概算であり、実際の使用量・トラフィックにより変動する
- AWS 料金は予告なく変更される場合がある
- 無料利用枠（Free Tier）は考慮していない
- Prod の ECS コストは Auto Scaling により最大 $900/月まで増加する可能性がある

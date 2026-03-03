# テスト戦略まとめ

> Next.js 15 / FastAPI / PostgreSQL / AWS (ECS Fargate + Aurora)

---

## テストフェーズの全体構成

ウォーターフォール開発における各テストフェーズの位置づけは以下の通りです。

| フェーズ | 目的 | 実施タイミング | 環境 |
|---|---|---|---|
| 単体テスト | 関数・コンポーネント単体の動作確認 | 実装と並行 | CI (GitHub Actions) |
| 結合テスト | コンポーネント間の連携確認 | 単体テスト完了後 | CI (GitHub Actions) |
| システムテスト（E2E） | ユーザーシナリオ全体の動作確認 | 結合テスト完了後 | Staging環境 |
| システムテスト（性能テスト） | SLA・ピーク負荷への耐性確認 | 結合テスト完了後〜システムテスト後半 | Staging環境（必須） |

### テスト内容サマリー

| レイヤー | 単体テスト | 結合テスト | システムテスト（E2E） | システムテスト（性能テスト） |
|---|---|---|---|---|
| **FE（Next.js 15）** | Client Componentの操作・zodバリデーション関数・ユーティリティ関数 | Server Actions〜APIの連携・エラーレスポンスの表示 | ユーザーシナリオ全体・画面遷移・権限・非機能（レスポンシブ・ブラウザ） | Lighthouseによる初期表示速度・Core Web Vitals |
| **BE（FastAPI）** | Domain層（Entity / Value Object / Domain Service）・Application層（Use Case） | APIエンドポイント（Presentation層）・Repository実装（Infrastructure層） | - | Locustによるストレス・スパイク・耐久テスト |
| **DB（Aurora / DynamoDB）** | - | CRUD・DB制約・リレーション・検索・GSI（DynamoDB） | - | スロークエリ調査・コネクション数監視 |
| **ツール** | Jest / pytest | Jest + MSW / pytest + TestClient | Playwright（または手動） | Locust / Lighthouse / CloudWatch |
| **実行環境** | CI (GitHub Actions) | CI (GitHub Actions) | Staging環境 | Staging環境（必須） |

---

# 詳細設計書 - GET /organizations/me — 自組織情報取得

## 基本情報

| 項目 | 内容 |
|---|---|
| エンドポイント | `GET /api/v1/organizations/me` |
| API設計 | [10_api-design.md](../10_api-design.md#get-organizationsme) |
| 機能要件 | [02_functional-requirements.md](../02_functional-requirements.md) |
| 業務フロー | [01_business-flow.md](../01_business-flow.md) |
| ユースケースクラス | `GetMyOrganizationUseCase` |
| 発行するドメインイベント | なし |
| トランザクション | なし（`organizations` テーブルの読み取りのみ） |
| 認可 | [08_role-permission.md](../08_role-permission.md) — A-02（組織管理者のみ） |
| テーブル定義 | [db-table-definition.md](../db-table-definition.md) — organizations |

---

## 概要

ログイン中のユーザーが所属する組織の詳細情報を取得する。JWT トークンに含まれる `organization_id` を使って自組織のレコードを返す。

---

## 事前条件・事後条件

### 事前条件

- 有効な JWT トークンが `Authorization` ヘッダーに付与されていること
- ログインユーザーのロールが `admin`（組織管理者）であること
- JWT に含まれる `organization_id` に対応する組織が `organizations` テーブルに存在すること

### 事後条件

- DB の状態は変化しない（読み取り専用）
- 自組織の情報がレスポンスとして返されること

---

## インターフェース定義

### リクエスト

パスパラメータ・クエリパラメータ・リクエストボディはすべてなし。

```
GET /api/v1/organizations/me
Authorization: Bearer <token>
```

### レスポンスボディ（200 OK）

| フィールド | 型 | 説明 |
|---|---|---|
| `id` | string | 組織ID（UUID） |
| `name` | string | 組織名 |
| `org_type` | string | 組織種別。`employment_support`：就労移行支援事業所 / `company`：企業 |
| `contact_email` | string | 連絡先メールアドレス |
| `contact_phone` | string\|null | 連絡先電話番号 |
| `address` | string\|null | 住所 |
| `is_active` | boolean | 有効フラグ |
| `created_at` | string | 作成日時（ISO 8601 UTC） |

```json
// 200 OK レスポンスサンプル
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "就労移行支援A事業所",
  "org_type": "employment_support",
  "contact_email": "info@example.com",
  "contact_phone": "03-1234-5678",
  "address": "東京都新宿区西新宿1-1-1",
  "is_active": true,
  "created_at": "2026-01-01T00:00:00Z"
}
```

---

## 使用するDBのテーブル

### organizations（利用組織）

| カラム | 型 | 用途 |
|---|---|---|
| `id` | UUID | JWT の `organization_id` と照合して対象レコードを特定する |
| `name` | VARCHAR(255) | レスポンスに含める |
| `org_type` | VARCHAR(50) | レスポンスに含める |
| `contact_email` | VARCHAR(255) | レスポンスに含める |
| `contact_phone` | VARCHAR(50) | レスポンスに含める |
| `address` | VARCHAR(500) | レスポンスに含める |
| `is_active` | BOOLEAN | レスポンスに含める |
| `created_at` | TIMESTAMP | レスポンスに含める |

**実行クエリ（概要）**

```sql
SELECT id, name, org_type, contact_email, contact_phone, address, is_active, created_at
FROM organizations
WHERE id = :organization_id;
```

---

## ビジネスルール

1. **自組織のみ参照可能**: ユーザーは JWT に含まれる `organization_id` に対応する組織の情報のみ取得できる。任意の組織 ID を指定して参照するエンドポイントは存在しない。

2. **組織管理者のみアクセス可能**: ロールが `staff`（担当者）のユーザーがリクエストした場合は `403 Forbidden` を返す。担当者は組織情報の参照権限を持たない。

3. **論理削除された組織の扱い**: `is_active = false` の組織に所属するユーザーはログイン自体が拒否されるため、このエンドポイントに到達する時点で `is_active = true` であることが保証される。ただし念のためレスポンスに `is_active` フィールドを含める。

---

## エラーケース

| エラーコード | HTTP | 条件 |
|---|---|---|
| `UNAUTHORIZED` | 401 | JWT トークンが存在しない、無効、または期限切れ |
| `FORBIDDEN` | 403 | ログインユーザーのロールが `staff`（担当者） |
| `ORGANIZATION_NOT_FOUND` | 404 | JWT の `organization_id` に対応する組織が存在しない（データ不整合） |

```json
// 401 UNAUTHORIZED
{
  "error": { "code": "UNAUTHORIZED", "message": "認証情報が無効です" }
}

// 403 FORBIDDEN
{
  "error": { "code": "FORBIDDEN", "message": "この操作は組織管理者のみ実行できます" }
}

// 404 ORGANIZATION_NOT_FOUND
{
  "error": { "code": "ORGANIZATION_NOT_FOUND", "message": "組織が見つかりません" }
}
```

---

## 変更履歴

| バージョン | 更新日 | 担当者 | 変更内容 |
|---|---|---|---|
| 1.0.0 | 2026-05-18 | - | 初版作成 |

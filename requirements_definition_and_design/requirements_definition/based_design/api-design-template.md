# API設計書

## 概要

{システム名}のREST API設計を定義します。
バックエンドはFastAPI（Python）で実装し、クリーンアーキテクチャパターンに従います。

---

## 基本仕様

| 項目 | 内容 |
|------|------|
| ベースURL | `/api/v1` |
| データ形式 | JSON（`Content-Type: application/json`） |
| 認証方式 | JWT Bearer Token（`Authorization: Bearer <token>`） |
| 文字コード | UTF-8 |
| タイムゾーン | UTC（フロントエンドでJSTに変換） |

---

## 認証

すべてのエンドポイントは認証が必要です（`/auth/login` と `/auth/password-reset` を除く）。
リクエストヘッダーに `Authorization: Bearer <token>` を付与してください。

### テナント分離

JWTトークンには `organization_id` を含み、すべてのAPIはログインユーザーの組織データのみを返します。

### システム管理者認証

`/admin/` プレフィックスのエンドポイントはシステム管理者専用です。システム管理者の JWT には `role: "system_admin"` が含まれ、`organization_id` は含まれません。一般ユーザーがアクセスした場合は `403 Forbidden` を返します。

---

## 共通レスポンス形式

### ページネーション付き一覧

```json
{
  "data": [...],
  "pagination": {
    "total": 100,
    "page": 1,
    "per_page": 20
  }
}
```

### エラーレスポンス

```json
{
  "detail": "エラーメッセージ"
}
```

### HTTPステータスコード

| コード | 意味 | 使用場面 |
|-------|------|---------|
| 200 | OK | GET・PUT成功 |
| 201 | Created | POST成功 |
| 204 | No Content | DELETE成功 |
| 400 | Bad Request | バリデーションエラー・不正な操作 |
| 401 | Unauthorized | 認証トークンなし・無効 |
| 403 | Forbidden | 権限不足 |
| 404 | Not Found | リソースが存在しない |
| 409 | Conflict | 重複・状態競合 |
| 422 | Unprocessable Entity | Pydanticバリデーションエラー |
| 500 | Internal Server Error | サーバーエラー |

---

## エンドポイント記述パターン

各エンドポイントは以下のパターンで記述します。

---

### 一覧取得（GET）

```
### GET `/{resources}`

{リソース名}一覧を取得する。

**クエリパラメータ**
| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `{param}` | string | {フィルター条件の説明} |
| `page` | int | ページ番号（デフォルト: 1） |
| `per_page` | int | 1ページ件数（デフォルト: 20） |

**レスポンス** `200 OK`
{
  "data": [
    {
      "id": "uuid",
      "{field1}": "{value1}",
      "{field2}": "{value2}",
      "created_at": "2026-01-01T00:00:00Z"
    }
  ],
  "pagination": { "total": 50, "page": 1, "per_page": 20 }
}

> {ロール別の返却範囲など補足事項があれば記載}

**権限**: {権限制限がある場合のみ記載}
```

---

### 新規作成（POST）

```
### POST `/{resources}`

{リソース名}を登録する。

**リクエスト**
{
  "{field1}": "{value1}",
  "{field2}": "{value2}"
}

> {補足事項があれば記載（例: 初期パスワードは自動生成）}

**レスポンス** `201 Created`
{
  "id": "uuid",
  "{field1}": "{value1}",
  "created_at": "2026-01-01T00:00:00Z"
}

**エラー**
- `409` {重複エラーの説明}

**権限**: {権限制限がある場合のみ記載}
```

---

### 詳細取得（GET）

```
### GET `/{resources}/{resource_id}`

{リソース名}の詳細を取得する。

**レスポンス** `200 OK`
{
  "id": "uuid",
  "{field1}": "{value1}",
  "{field2}": "{value2}",
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z"
}
```

---

### 更新（PUT / PATCH）

```
### PUT `/{resources}/{resource_id}`

{リソース名}を更新する。

**リクエスト**（更新するフィールドのみ）
{
  "{field1}": "{updated_value}"
}

**レスポンス** `200 OK`

**エラー**
- `400` {更新不可の条件（例: 確定済みのため編集不可）}

**権限**: {権限制限がある場合のみ記載}
```

---

### 削除（DELETE）

```
### DELETE `/{resources}/{resource_id}`

{リソース名}を削除する（使用中の場合は論理削除）。

**レスポンス** `204 No Content`

**エラー**
- `409` {削除不可の条件}
```

---

### アクション系（POST）

リソースの状態遷移など、CRUD に収まらない操作。

```
### POST `/{resources}/{resource_id}/{action}`

{リソース名}を{アクション名}にする。

**リクエスト**（body不要、または下記）
{
  "{field}": "{value}"
}

**レスポンス** `200 OK`
{
  "id": "uuid",
  "status": "{new_status}"
}

**エラー**
- `400` {実行不可の条件（例: 必須項目が未入力）}
```

---

## エンドポイント一覧

```
# 認証
POST   /auth/login
POST   /auth/logout
POST   /auth/password-reset/request
POST   /auth/password-reset/confirm

# {グループ名}
GET    /{resources}
POST   /{resources}
GET    /{resources}/{resource_id}
PUT    /{resources}/{resource_id}
DELETE /{resources}/{resource_id}
POST   /{resources}/{resource_id}/{action}

# システム管理（admin のみ）
POST   /admin/{resources}
GET    /admin/{resources}
GET    /admin/{resources}/{resource_id}
PUT    /admin/{resources}/{resource_id}
PATCH  /admin/{resources}/{resource_id}/status
```

---

## ディレクトリ構成（実装時の参考）

```
backend/app/
├── api/v1/endpoints/
│   ├── auth.py
│   └── {resource}.py
├── schemas/
│   ├── auth.py
│   └── {resource}.py
├── application/
│   ├── auth/
│   └── {resource}/
└── domain/
    ├── auth/
    └── {resource}/
```

# API設計書

## 概要

障害者雇用支援アセスメントシステムのREST API設計を定義します。
バックエンドはFastAPI（Python）で実装し、既存のプロジェクトテンプレートのクリーンアーキテクチャパターンに従います。

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

## 1. 認証（Auth）

### POST `/auth/login`

ログイン。

**リクエスト**
```json
{
  "email": "yamada@example.com",
  "password": "Password123!"
}
```

**レスポンス** `200 OK`
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "name": "山田 太郎",
    "email": "yamada@example.com",
    "role": "staff",
    "organization_id": "uuid",
    "organization_name": "就労移行支援A事業所"
  }
}
```

**エラー**
- `401` 認証失敗（メールアドレスまたはパスワードが違います）
- `423` アカウントロック（ログイン試行上限超過）

---

### POST `/auth/logout`

ログアウト（トークン無効化）。

**レスポンス** `204 No Content`

---

### POST `/auth/password-reset/request`

パスワードリセットメールの送信。

**リクエスト**
```json
{
  "email": "yamada@example.com"
}
```

**レスポンス** `200 OK`
```json
{
  "message": "パスワードリセット用のメールを送信しました。"
}
```

> メールアドレスが存在しない場合も同じレスポンスを返す（ユーザー列挙攻撃対策）

---

### POST `/auth/password-reset/confirm`

新しいパスワードを設定する。

**リクエスト**
```json
{
  "token": "reset-token-from-email",
  "new_password": "NewPassword456!"
}
```

**レスポンス** `200 OK`

**エラー**
- `400` トークンが無効または期限切れ

---

## 2. 組織・ユーザー管理（Organizations / Users）

### GET `/organizations/me`

自組織の情報を取得する。

**レスポンス** `200 OK`
```json
{
  "id": "uuid",
  "name": "就労移行支援A事業所",
  "org_type": "employment_support",
  "contact_email": "info@example.com",
  "contact_phone": "03-1234-5678",
  "address": "東京都新宿区...",
  "created_at": "2026-01-01T00:00:00Z"
}
```

**権限**: 組織管理者のみ

---

### PUT `/organizations/me`

自組織の情報を更新する。

**リクエスト**
```json
{
  "name": "就労移行支援A事業所",
  "contact_email": "info@example.com",
  "contact_phone": "03-1234-5678",
  "address": "東京都新宿区..."
}
```

**レスポンス** `200 OK`（更新後の組織情報）

**権限**: 組織管理者のみ

---

### GET `/users`

担当者一覧を取得する。

**クエリパラメータ**
| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `is_active` | boolean | 有効/無効フィルター（省略時: 全件） |
| `page` | int | ページ番号（デフォルト: 1） |
| `per_page` | int | 1ページ件数（デフォルト: 20, 最大: 100） |

**レスポンス** `200 OK`
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "山田 太郎",
      "email": "yamada@example.com",
      "role": "staff",
      "is_active": true,
      "created_at": "2026-01-01T00:00:00Z"
    }
  ],
  "pagination": { "total": 10, "page": 1, "per_page": 20 }
}
```

**権限**: 組織管理者のみ

---

### POST `/users`

担当者アカウントを登録する。

**リクエスト**
```json
{
  "name": "鈴木 次郎",
  "email": "suzuki@example.com",
  "role": "staff"
}
```

> 初期パスワードはシステムが自動生成しメールで送信する

**レスポンス** `201 Created`
```json
{
  "id": "uuid",
  "name": "鈴木 次郎",
  "email": "suzuki@example.com",
  "role": "staff",
  "is_active": true,
  "created_at": "2026-03-30T00:00:00Z"
}
```

**エラー**
- `409` メールアドレスが既に使用されている

**権限**: 組織管理者のみ

---

### GET `/users/{user_id}`

担当者の詳細を取得する。

**レスポンス** `200 OK`（ユーザー情報）

**権限**: 組織管理者のみ

---

### PUT `/users/{user_id}`

担当者情報を更新する。

**リクエスト**
```json
{
  "name": "鈴木 次郎",
  "role": "admin",
  "is_active": true
}
```

**レスポンス** `200 OK`

**権限**: 組織管理者のみ

---

## 3. 支援対象者管理（Clients）

### GET `/clients`

支援対象者一覧を取得する。

**クエリパラメータ**
| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `assigned_user_id` | uuid | 担当者でフィルター |
| `disability_type` | string | 障害種別でフィルター |
| `page` | int | ページ番号 |
| `per_page` | int | 件数 |

> 担当者ロールは自分がアサインされた対象者のみ返す

**レスポンス** `200 OK`
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "鈴木 花子",
      "disability_type": "mental",
      "assigned_user": {
        "id": "uuid",
        "name": "山田 太郎"
      },
      "latest_assessment_date": "2026-03-20",
      "latest_assessment_status": "completed",
      "created_at": "2026-01-15T00:00:00Z"
    }
  ],
  "pagination": { "total": 50, "page": 1, "per_page": 20 }
}
```

---

### POST `/clients`

支援対象者を登録する。

**リクエスト**
```json
{
  "name": "田中 三郎",
  "birth_date": "1990-04-15",
  "disability_type": "developmental",
  "diagnosis_name": "ASD（自閉スペクトラム症）",
  "work_experience": "IT企業で3年間システム運用を担当。体調不良により退職。",
  "desired_job_type": "事務・データ入力",
  "assigned_user_id": "uuid"
}
```

**レスポンス** `201 Created`（登録した対象者情報）

---

### GET `/clients/{client_id}`

支援対象者の詳細を取得する。

**レスポンス** `200 OK`
```json
{
  "id": "uuid",
  "name": "鈴木 花子",
  "birth_date": "1995-08-22",
  "disability_type": "mental",
  "diagnosis_name": "うつ病・不安障害",
  "work_experience": "...",
  "desired_job_type": "一般事務",
  "assigned_user": {
    "id": "uuid",
    "name": "山田 太郎"
  },
  "latest_assessment": {
    "id": "uuid",
    "status": "completed",
    "assessed_at": "2026-03-20T10:00:00Z"
  },
  "assessment_count": 2,
  "support_plan_count": 1,
  "created_at": "2026-01-15T00:00:00Z",
  "updated_at": "2026-03-20T10:00:00Z"
}
```

---

### PUT `/clients/{client_id}`

支援対象者の情報を更新する。

**リクエスト**（更新するフィールドのみ）
```json
{
  "desired_job_type": "データ入力・軽作業",
  "work_experience": "更新内容..."
}
```

**レスポンス** `200 OK`

---

### PATCH `/clients/{client_id}/assigned-user`

担当者を変更する。

**リクエスト**
```json
{
  "assigned_user_id": "uuid"
}
```

**レスポンス** `200 OK`

**権限**: 組織管理者のみ

---

## 4. アセスメント（Assessments）

### POST `/clients/{client_id}/assessments`

アセスメントを新規作成する。

**リクエスト**（body不要、空オブジェクトでも可）

**レスポンス** `201 Created`
```json
{
  "id": "uuid",
  "client_id": "uuid",
  "evaluator_id": "uuid",
  "status": "in_progress",
  "scores": [],
  "created_at": "2026-03-30T09:00:00Z"
}
```

---

### GET `/clients/{client_id}/assessments`

アセスメント履歴一覧を取得する。

**クエリパラメータ**
| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `page` | int | ページ番号 |
| `per_page` | int | 件数 |

**レスポンス** `200 OK`
```json
{
  "data": [
    {
      "id": "uuid",
      "status": "completed",
      "layer_scores": {
        "layer1": 4.2,
        "layer2": 3.6,
        "layer3": 2.8,
        "layer4": 3.2,
        "layer5": 2.4
      },
      "assessed_at": "2026-03-20T10:00:00Z",
      "evaluator": { "id": "uuid", "name": "山田 太郎" }
    }
  ],
  "pagination": { "total": 3, "page": 1, "per_page": 20 }
}
```

---

### GET `/assessments/{assessment_id}`

アセスメントの詳細（全スコア）を取得する。

**レスポンス** `200 OK`
```json
{
  "id": "uuid",
  "client_id": "uuid",
  "status": "in_progress",
  "evaluator_comment": "",
  "scores": [
    {
      "layer_number": 1,
      "item_key": "layer1_physical_stability",
      "item_name": "体調の安定性",
      "score": 4,
      "item_comment": ""
    },
    {
      "layer_number": 1,
      "item_key": "layer1_medication",
      "item_name": "服薬管理",
      "score": null,
      "item_comment": ""
    }
  ],
  "layer_scores": {
    "layer1": null,
    "layer2": null,
    "layer3": null,
    "layer4": null,
    "layer5": null
  },
  "assessed_at": null,
  "created_at": "2026-03-30T09:00:00Z",
  "updated_at": "2026-03-30T09:30:00Z"
}
```

---

### PUT `/assessments/{assessment_id}/scores`

評価スコアを一括保存する（一時保存・上書き）。

**リクエスト**
```json
{
  "evaluator_comment": "第3層・第5層に課題あり。",
  "scores": [
    {
      "item_key": "layer1_physical_stability",
      "score": 4,
      "item_comment": ""
    },
    {
      "item_key": "layer1_medication",
      "score": null,
      "item_comment": "服薬なし"
    }
  ]
}
```

**レスポンス** `200 OK`（更新後のアセスメント詳細）

**エラー**
- `400` アセスメントが既に完了している（`status: completed`）
- `400` 不正な `item_key`

---

### POST `/assessments/{assessment_id}/complete`

アセスメントを完了にする。

**リクエスト**（body不要）

> 全必須項目が入力済みであることを検証してから完了にする

**レスポンス** `200 OK`
```json
{
  "id": "uuid",
  "status": "completed",
  "layer_scores": {
    "layer1": 4.2,
    "layer2": 3.6,
    "layer3": 2.8,
    "layer4": 3.2,
    "layer5": 2.4
  },
  "assessed_at": "2026-03-30T10:00:00Z"
}
```

**エラー**
- `400` 未入力の必須評価項目がある

---

## 5. レポート（Reports）

### GET `/assessments/{assessment_id}/report`

診断レポートデータを取得する。

**クエリパラメータ**
| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `compare_with` | uuid | 比較対象のアセスメントID（省略時は自動で直前のアセスメントを使用） |

**レスポンス** `200 OK`
```json
{
  "assessment": {
    "id": "uuid",
    "assessed_at": "2026-03-20T10:00:00Z",
    "evaluator": { "id": "uuid", "name": "山田 太郎" },
    "evaluator_comment": "..."
  },
  "client": {
    "id": "uuid",
    "name": "鈴木 花子"
  },
  "layer_scores": {
    "layer1": 4.2,
    "layer2": 3.6,
    "layer3": 2.8,
    "layer4": 3.2,
    "layer5": 2.4
  },
  "previous": {
    "assessment_id": "uuid",
    "assessed_at": "2025-09-15T10:00:00Z",
    "layer_scores": {
      "layer1": 3.8,
      "layer2": 3.4,
      "layer3": 3.0,
      "layer4": 2.8,
      "layer5": 2.2
    },
    "diff": {
      "layer1": 0.4,
      "layer2": 0.2,
      "layer3": -0.2,
      "layer4": 0.4,
      "layer5": 0.2
    }
  },
  "low_score_layers": [3, 5]
}
```

**エラー**
- `400` アセスメントが未完了

---

### GET `/assessments/{assessment_id}/report/pdf`

診断レポートをPDFでダウンロードする。

**レスポンス** `200 OK`
- `Content-Type: application/pdf`
- `Content-Disposition: attachment; filename="report_{client_name}_{date}.pdf"`

---

## 6. 支援計画（Support Plans）

### GET `/assessments/{assessment_id}/training-suggestions`

アセスメント結果に基づくトレーニング提案を取得する。

**レスポンス** `200 OK`
```json
{
  "low_score_layers": [3, 5],
  "suggestions": [
    {
      "layer_number": 3,
      "layer_name": "対人技能",
      "layer_score": 2.8,
      "training_menus": [
        {
          "id": "uuid",
          "name": "コミュニケーション基礎トレーニング",
          "format": "group",
          "duration_minutes": 60,
          "description": "...",
          "achievement_goal": "..."
        }
      ]
    }
  ]
}
```

---

### POST `/clients/{client_id}/support-plans`

個別支援計画を新規作成する（一時保存）。

**リクエスト**
```json
{
  "assessment_id": "uuid",
  "title": "鈴木 花子 個別支援計画 第2版（2026年3月）",
  "plan_start_date": "2026-04-01",
  "plan_end_date": "2026-09-30",
  "goal": "対人コミュニケーション力の向上と職場適応力の強化を通じて、6ヶ月以内の就労移行を目指す。",
  "training_menu_ids": ["uuid1", "uuid2", "uuid3"],
  "support_manual_ids": ["uuid1", "uuid2"],
  "accommodation_notes": "定期的な1on1面談の設定、指示は文書で提示。",
  "remarks": ""
}
```

**レスポンス** `201 Created`
```json
{
  "id": "uuid",
  "version": 2,
  "status": "draft",
  "title": "...",
  "created_at": "2026-03-30T11:00:00Z"
}
```

---

### GET `/clients/{client_id}/support-plans`

個別支援計画の履歴一覧を取得する。

**レスポンス** `200 OK`
```json
{
  "data": [
    {
      "id": "uuid",
      "version": 2,
      "title": "個別支援計画 第2版（2026年3月）",
      "plan_start_date": "2026-04-01",
      "plan_end_date": "2026-09-30",
      "status": "confirmed",
      "author": { "id": "uuid", "name": "山田 太郎" },
      "created_at": "2026-03-30T11:00:00Z"
    }
  ],
  "pagination": { "total": 2, "page": 1, "per_page": 20 }
}
```

---

### GET `/support-plans/{plan_id}`

個別支援計画の詳細を取得する。

**レスポンス** `200 OK`
```json
{
  "id": "uuid",
  "version": 2,
  "status": "confirmed",
  "title": "...",
  "plan_start_date": "2026-04-01",
  "plan_end_date": "2026-09-30",
  "goal": "...",
  "training_menus": [
    { "id": "uuid", "name": "コミュニケーション基礎トレーニング", "target_layer": 3 }
  ],
  "support_manuals": [
    { "id": "uuid", "name": "精神障害者コミュニケーション支援マニュアル" }
  ],
  "accommodation_notes": "...",
  "remarks": "",
  "author": { "id": "uuid", "name": "山田 太郎" },
  "created_at": "2026-03-30T11:00:00Z",
  "updated_at": "2026-03-30T12:00:00Z"
}
```

---

### PUT `/support-plans/{plan_id}`

個別支援計画を更新する（一時保存）。

**リクエスト**（更新するフィールドのみ）

**レスポンス** `200 OK`

**エラー**
- `400` 確定済みの計画書は編集不可（`status: confirmed`）

---

### POST `/support-plans/{plan_id}/confirm`

個別支援計画を確定する。

**レスポンス** `200 OK`
```json
{
  "id": "uuid",
  "version": 2,
  "status": "confirmed"
}
```

**エラー**
- `400` 必須項目が未入力
- `400` 既に確定済み

---

### GET `/support-plans/{plan_id}/pdf`

個別支援計画書をPDFでダウンロードする。

**レスポンス** `200 OK`
- `Content-Type: application/pdf`
- `Content-Disposition: attachment; filename="support_plan_{client_name}_v{version}.pdf"`

---

## 7. マスタ管理（Training Menus / Support Manuals）

### GET `/training-menus`

トレーニングメニュー一覧を取得する。

**クエリパラメータ**
| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `target_layer` | int (1-5) | 層でフィルター |
| `is_active` | boolean | 有効/無効フィルター（デフォルト: true） |
| `page` | int | ページ番号 |
| `per_page` | int | 件数 |

**レスポンス** `200 OK`
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "コミュニケーション基礎トレーニング",
      "target_layer": 3,
      "format": "group",
      "duration_minutes": 60,
      "description": "...",
      "achievement_goal": "...",
      "is_active": true,
      "created_by": { "id": "uuid", "name": "山田 太郎" },
      "created_at": "2026-01-10T00:00:00Z"
    }
  ],
  "pagination": { "total": 12, "page": 1, "per_page": 20 }
}
```

---

### POST `/training-menus`

トレーニングメニューを登録する。

**リクエスト**
```json
{
  "name": "就労体験プログラム（模擬職場）",
  "target_layer": 5,
  "format": "practical",
  "duration_minutes": 120,
  "description": "実際の職場に近い環境で作業を体験するプログラム。",
  "achievement_goal": "就労場面における自分の特性・課題を把握し、対処法を身につける。"
}
```

**レスポンス** `201 Created`

---

### GET `/training-menus/{menu_id}`

トレーニングメニューの詳細を取得する。

**レスポンス** `200 OK`

---

### PUT `/training-menus/{menu_id}`

トレーニングメニューを更新する。

**レスポンス** `200 OK`

**権限**: 組織管理者は全件。担当者は自作成のみ。

---

### DELETE `/training-menus/{menu_id}`

トレーニングメニューを削除する（支援計画で使用中の場合は論理削除）。

**レスポンス** `204 No Content`

**エラー**
- `409` 支援計画で使用中のため削除不可（`is_active = false` に変更）

---

### GET `/support-manuals`

支援マニュアル一覧を取得する。

**クエリパラメータ**
| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `disability_type` | string | 障害種別でフィルター |
| `target_scene` | string | 場面でフィルター |
| `is_active` | boolean | 有効/無効フィルター（デフォルト: true） |
| `page` | int | ページ番号 |
| `per_page` | int | 件数 |

**レスポンス** `200 OK`（トレーニングメニューと同形式）

---

### POST `/support-manuals`

支援マニュアルを登録する。

**リクエスト**
```json
{
  "name": "精神障害者コミュニケーション支援マニュアル",
  "description": "精神疾患を抱えながら職場コミュニケーションを行う際の支援手順。",
  "disability_types": ["mental"],
  "target_scene": "職場コミュニケーション",
  "procedure": "1. 状況の確認...\n2. 具体的な対処法の提示...",
  "notes": "感情的になっている場合はまず落ち着くことを優先する。"
}
```

**レスポンス** `201 Created`

---

### PUT `/support-manuals/{manual_id}`

支援マニュアルを更新する。

**レスポンス** `200 OK`

**権限**: 組織管理者は全件。担当者は自作成のみ。

---

### DELETE `/support-manuals/{manual_id}`

支援マニュアルを削除する（使用中の場合は論理削除）。

**レスポンス** `204 No Content`

---

## 8. エンドポイント一覧

```
# 認証
POST   /auth/login
POST   /auth/logout
POST   /auth/password-reset/request
POST   /auth/password-reset/confirm

# 組織・ユーザー管理
GET    /organizations/me
PUT    /organizations/me
GET    /users
POST   /users
GET    /users/{user_id}
PUT    /users/{user_id}

# 支援対象者
GET    /clients
POST   /clients
GET    /clients/{client_id}
PUT    /clients/{client_id}
PATCH  /clients/{client_id}/assigned-user

# アセスメント
POST   /clients/{client_id}/assessments
GET    /clients/{client_id}/assessments
GET    /assessments/{assessment_id}
PUT    /assessments/{assessment_id}/scores
POST   /assessments/{assessment_id}/complete

# レポート
GET    /assessments/{assessment_id}/report
GET    /assessments/{assessment_id}/report/pdf

# 支援計画
GET    /assessments/{assessment_id}/training-suggestions
POST   /clients/{client_id}/support-plans
GET    /clients/{client_id}/support-plans
GET    /support-plans/{plan_id}
PUT    /support-plans/{plan_id}
POST   /support-plans/{plan_id}/confirm
GET    /support-plans/{plan_id}/pdf

# マスタ管理
GET    /training-menus
POST   /training-menus
GET    /training-menus/{menu_id}
PUT    /training-menus/{menu_id}
DELETE /training-menus/{menu_id}
GET    /support-manuals
POST   /support-manuals
GET    /support-manuals/{manual_id}
PUT    /support-manuals/{manual_id}
DELETE /support-manuals/{manual_id}
```

---

## 9. ディレクトリ構成（実装時の参考）

既存のプロジェクトテンプレートのパターンに従い、以下の構成で実装します。

```
backend/app/
├── api/v1/endpoints/
│   ├── auth.py
│   ├── organizations.py
│   ├── users.py
│   ├── clients.py
│   ├── assessments.py
│   ├── reports.py
│   ├── support_plans.py
│   ├── training_menus.py
│   └── support_manuals.py
├── schemas/
│   ├── auth.py
│   ├── user.py
│   ├── client.py
│   ├── assessment.py
│   ├── report.py
│   ├── support_plan.py
│   ├── training_menu.py
│   └── support_manual.py
├── application/
│   ├── auth/
│   ├── user/
│   ├── client/
│   ├── assessment/
│   ├── support_plan/
│   └── master/
└── domain/
    ├── user/
    ├── client/
    ├── assessment/
    ├── support_plan/
    └── master/
```

# データモデル図

## 概要

{システム名}の主要エンティティとそのリレーションを定義します。

---

## 1. ER図

```mermaid
erDiagram

    Organization {
        uuid id PK
        string name
        string contact_email
        string contact_phone
        string address
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    User {
        uuid id PK
        uuid organization_id FK
        string name
        string email
        string password_hash
        enum role "admin / staff"
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    %% ここにプロジェクト固有のエンティティを追加する
    {Entity1} {
        uuid id PK
        uuid organization_id FK
        string {field1}
        string {field2}
        enum status "{status1} / {status2}"
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    {Entity2} {
        uuid id PK
        uuid {entity1_id} FK
        string {field1}
        int {field2}
        datetime created_at
        datetime updated_at
    }

    %% 中間テーブルの例
    {Entity1Entity2} {
        uuid id PK
        uuid {entity1_id} FK
        uuid {entity2_id} FK
        int sort_order
    }

    Organization ||--o{ User : "has"
    Organization ||--o{ {Entity1} : "owns"

    User ||--o{ {Entity1} : "{relation}"

    {Entity1} ||--o{ {Entity2} : "has"
    {Entity1} ||--o{ {Entity1Entity2} : "includes"
    {Entity2} ||--o{ {Entity1Entity2} : "referenced_by"
```

---

## 2. エンティティ定義

### Organization（利用組織）

| カラム | 型 | 説明 |
|-------|-----|------|
| id | UUID | 主キー |
| name | STRING | 組織名 |
| contact_email | STRING | 連絡先メールアドレス |
| contact_phone | STRING | 連絡先電話番号 |
| address | STRING | 住所 |
| is_active | BOOLEAN | 有効フラグ |
| created_at / updated_at | DATETIME | 作成・更新日時 |

---

### User（ユーザー）

| カラム | 型 | 説明 |
|-------|-----|------|
| id | UUID | 主キー |
| organization_id | UUID FK | 所属組織 |
| name | STRING | 氏名 |
| email | STRING | メールアドレス（ログインID） |
| password_hash | STRING | ハッシュ化パスワード |
| role | ENUM | ロール（`admin`：組織管理者 / `staff`：一般ユーザー） |
| is_active | BOOLEAN | 有効フラグ（無効化で論理削除） |
| created_at / updated_at | DATETIME | 作成・更新日時 |

**ユニーク制約：** `email`

---

### {Entity1}（{エンティティ説明}）

| カラム | 型 | 説明 |
|-------|-----|------|
| id | UUID | 主キー |
| organization_id | UUID FK | 所属組織 |
| {field1} | STRING | {説明} |
| {field2} | ENUM | {説明}（`{value1}` / `{value2}`） |
| status | ENUM | 状態（`{status1}`：{説明} / `{status2}`：{説明}） |
| is_active | BOOLEAN | 有効フラグ |
| created_at / updated_at | DATETIME | 作成・更新日時 |

---

### {Entity2}（{エンティティ説明}）

| カラム | 型 | 説明 |
|-------|-----|------|
| id | UUID | 主キー |
| {entity1_id} | UUID FK | {参照先エンティティ} |
| {field1} | STRING | {説明} |
| {field2} | INT | {説明} |
| created_at / updated_at | DATETIME | 作成・更新日時 |

**ユニーク制約：** `({entity1_id}, {field1})`

---

### {Entity1Entity2}（{エンティティ説明}）

中間テーブル。{説明}。

| カラム | 型 | 説明 |
|-------|-----|------|
| id | UUID | 主キー |
| {entity1_id} | UUID FK | {Entity1} |
| {entity2_id} | UUID FK | {Entity2} |
| sort_order | INT | 表示順 |

---

## 3. テナント分離方針

本システムはマルチテナント構成を採用し、すべてのデータは `organization_id` によって組織ごとに分離する。

```mermaid
flowchart LR
    subgraph "組織A"
        A_User[ユーザー]
        A_Entity1[{Entity1}]
    end
    subgraph "組織B"
        B_User[ユーザー]
        B_Entity1[{Entity1}]
    end

    Org_A[Organization A] --> A_User
    Org_A --> A_Entity1

    Org_B[Organization B] --> B_User
    Org_B --> B_Entity1
```

- すべてのクエリに `organization_id` の絞り込みを必須とする
- 異なる組織のデータは API レベルで相互参照不可とする
- `Organization` テーブルのみシステム管理者が管理する

---

## 4. 主要なビジネスルール

| # | ルール |
|---|--------|
| 1 | {ビジネスルール} |
| 2 | {ステータス遷移ルール（例: status = completed になると更新不可）} |
| 3 | {バージョン管理ルール（例: 同一 client_id 内で自動採番）} |
| 4 | {論理削除ルール（例: 参照中のレコードがある場合は is_active = false のみ許可）} |
| 5 | {外部キー整合性ルール（例: assigned_user_id は同一 organization_id の User のみ設定可能）} |

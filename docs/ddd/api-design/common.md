# API共通仕様 - 注文管理システム（OrderHub）

## ベースURL
```
/api/v1
```

## レスポンス形式
すべてのレスポンスはJSON形式で返却する。

### 成功レスポンス
```json
{
  "data": { ... }
}
```

### 一覧レスポンス
```json
{
  "data": [ ... ],
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
  "error": {
    "code": "ORDER_NOT_FOUND",
    "message": "指定された注文が見つかりません"
  }
}
```

## 共通エラーコード
| HTTPステータス | エラーコード | 説明 |
|--------------|-------------|------|
| 400 | VALIDATION_ERROR | リクエストパラメータ不正 |
| 404 | RESOURCE_NOT_FOUND | リソースが見つからない |
| 409 | CONFLICT | ビジネスルール違反（状態遷移エラー等） |
| 500 | INTERNAL_ERROR | サーバー内部エラー |

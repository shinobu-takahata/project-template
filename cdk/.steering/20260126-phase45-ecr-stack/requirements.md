# フェーズ4.5: ECRスタック - 要求内容

## 背景
現在のComputeStackでは、ECRリポジトリとECSサービスが同一スタック内に存在します。
この構成では、初回デプロイ時に以下の問題が発生します：

- ECRリポジトリとECSサービスが同時に作成される
- ECSサービスのdesiredCount > 0の場合、タスク定義に指定されたイメージがECRに存在しないためタスクが起動できない
- 結果として、スタックのデプロイが失敗するか、desiredCount=0で一旦デプロイしてイメージプッシュ後に更新する必要がある

## 目的
ECRリポジトリを独立したスタック（EcrStack）として分離し、以下を実現する：

1. **デプロイ順序の制御**
   - EcrStack → イメージプッシュ → ComputeStack の順でデプロイ可能
   - ComputeStackデプロイ時には必ずECRにイメージが存在する状態

2. **ライフサイクルの分離**
   - ECRリポジトリ: 静的（削除/再作成が少ない）
   - ECSサービス: 動的（頻繁に更新される）

3. **マルチ環境対応**
   - dev/prod環境ごとに独立したECRリポジトリを作成
   - 環境間でのイメージ共有も可能な設計

## 要求機能

### 1. ECRリポジトリの作成
- 環境ごとのECRリポジトリ（`backend-{env}`）
- イメージスキャン設定（脆弱性検出）
- ライフサイクルポリシー（古いイメージの自動削除）
- 暗号化設定（AES256）
- RemovalPolicy: RETAIN（誤削除防止）

### 2. スタック間連携
- ECRリポジトリURIをCfnOutputでエクスポート
- ComputeStackからFn.importValueで参照可能

### 3. CI/CD統合の準備
- GitHub ActionsからのECRプッシュ権限設定
- OIDC認証基盤との連携

## 受け入れ条件

1. **EcrStackの独立性**
   - [ ] EcrStackが他のスタックに依存せず、単独でデプロイ可能
   - [ ] ECRリポジトリが正常に作成される

2. **スタック間連携**
   - [ ] ECRリポジトリURIがCfnOutputでエクスポートされる
   - [ ] ComputeStackから参照可能

3. **セキュリティ要件**
   - [ ] イメージスキャンが有効化されている
   - [ ] 暗号化が有効化されている
   - [ ] RemovalPolicyがRETAINに設定されている

4. **ビルド検証**
   - [ ] `npm run build` が成功する
   - [ ] `cdk synth` が成功する
   - [ ] `cdk diff` でEcrStackの変更内容が確認できる

## 制約事項

### 技術的制約
- ECRリポジトリ名は一意である必要がある
- ECRリポジトリは削除後も一定期間名前が予約される
- イメージサイズの上限は10GB

### 運用制約
- 初回デプロイ後、手動でダミーイメージをプッシュする必要がある
- または、CI/CDパイプラインで自動的にイメージをビルド・プッシュする

## 影響範囲

### 新規作成
- `lib/stacks/ecr-stack.ts` - EcrStack本体
- `.steering/20260126-phase45-ecr-stack/` - ステアリングドキュメント

### 変更対象
- `bin/app.ts` - EcrStackの追加、依存関係設定
- `.steering/20260123-phase5-compute-stack/design.md` - ECR部分の削除、EcrStack参照の追加
- `.steering/20260123-phase5-compute-stack/tasklist.md` - ECR関連タスクの削除
- `.steering/20260126-phase7-cicd-integration/design.md` - ECRリポジトリ参照の更新

### 影響を受けるスタック
- ComputeStack: ECRリポジトリの参照方法が変更
- (将来) CI/CDスタック: ECRリポジトリへのアクセス権限設定

## 非機能要件

### パフォーマンス
- イメージプル速度: VPCエンドポイント経由で高速化

### コスト
- イメージストレージ: ライフサイクルポリシーで最適化
- データ転送: VPCエンドポイント経由で無料

### 可用性
- ECRはマネージドサービスで高可用性

## 参考情報
- [AWS CDK - ECR Module](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_ecr-readme.html)
- [ECR Repository Best Practices](https://docs.aws.amazon.com/AmazonECR/latest/userguide/best-practices.html)

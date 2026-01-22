# フェーズ1: CDK基盤セットアップ - 要求事項

## 概要
AWS CDKプロジェクトの初期化と基本構造の構築を行います。本フェーズでは、CDKプロジェクトの土台となる設定ファイル、ディレクトリ構造、環境設定を整備します。

## 目的
- AWS CDKプロジェクトの基本構造を作成する
- 開発環境（dev）と本番環境（prod）の設定を定義する
- 後続フェーズでのスタック実装の基盤を整える

## スコープ

### 含まれるもの
1. **CDKプロジェクト初期化**
   - TypeScriptベースのCDKプロジェクト構造
   - 必要なディレクトリの作成（`lib/stacks/`, `lib/constructs/`, `lib/config/`）
   - 依存関係の定義（package.json）
   - TypeScript設定（tsconfig.json）
   - CDK設定（cdk.json）

2. **環境設定ファイル**
   - 環境設定の型定義（EnvConfig）
   - 開発環境設定（dev.ts）
   - 本番環境設定（prod.ts）
   - 環境設定取得関数

### 含まれないもの
- 実際のAWSリソース（VPC、ECS、Auroraなど）の作成
- スタックの実装（NetworkStack、SecurityStackなど）
- AWSへのデプロイ

## 機能要件

### FR-1: CDKプロジェクト構造
- **FR-1.1**: `cdk/`ディレクトリ配下に標準的なCDKプロジェクト構造を作成
- **FR-1.2**: `bin/app.ts`をエントリーポイントとして定義
- **FR-1.3**: `lib/stacks/`, `lib/constructs/`, `lib/config/`ディレクトリを作成

### FR-2: 依存関係管理
- **FR-2.1**: `package.json`に必要なCDK関連パッケージを定義
  - `aws-cdk-lib` (^2.120.0)
  - `constructs` (^10.0.0)
- **FR-2.2**: 開発用パッケージを定義
  - `@types/node` (^20.0.0)
  - `typescript` (^5.0.0)
  - `aws-cdk` (^2.120.0)

### FR-3: TypeScript設定
- **FR-3.1**: `tsconfig.json`でTypeScriptコンパイラオプションを定義
  - target: ES2020
  - module: commonjs
  - strict: true
  - esModuleInterop: true

### FR-4: CDK設定
- **FR-4.1**: `cdk.json`でCDKの動作設定を定義
  - アプリケーションエントリーポイント: `node bin/app.js`
  - Context値（環境変数の受け渡し）

### FR-5: 環境設定
- **FR-5.1**: 環境設定の型定義（EnvConfig型）を作成
  - 環境名（dev/prod）
  - リージョン（ap-northeast-1）
  - VPC CIDR、サブネットCIDR
  - ECSリソース設定（CPU、メモリ、タスク数）
  - Auroraインスタンスクラス、バックアップ設定
  - ログ保持期間
  - ドメイン名
  - VPCエンドポイント使用フラグ

- **FR-5.2**: 開発環境設定（`config/dev.ts`）
  - VPC CIDR: 10.0.0.0/16
  - ECS: CPU 512, Memory 1024, desiredCount 2
  - Aurora: db.t4g.medium, backupRetentionDays 7
  - ログ保持期間: 7日
  - 削除保護: 無効

- **FR-5.3**: 本番環境設定（`config/prod.ts`）
  - VPC CIDR: 10.1.0.0/16
  - ECS: CPU 1024, Memory 2048, desiredCount 2
  - Aurora: db.r6g.large, backupRetentionDays 30
  - ログ保持期間: 30日
  - 削除保護: 有効

- **FR-5.4**: 環境設定取得関数（`getEnvConfig`）
  - 引数で環境名（dev/prod）を受け取り、対応する設定を返す

### FR-6: エントリーポイント（bin/app.ts）
- **FR-6.1**: CDKアプリケーションの初期化
- **FR-6.2**: Context値から環境名を取得（デフォルト: dev）
- **FR-6.3**: 環境設定の読み込み
- **FR-6.4**: スタック作成の準備（実際のスタック作成は後続フェーズ）

## 非機能要件

### NFR-1: 保守性
- コードは明確にコメントされ、意図が理解しやすいこと
- ディレクトリ構造は標準的なCDKプロジェクトパターンに従うこと

### NFR-2: 拡張性
- 新しい環境設定を追加しやすい構造であること
- 環境固有のパラメータを一元管理できること

### NFR-3: 型安全性
- TypeScriptの型システムを活用し、コンパイル時に設定ミスを検出できること

## 制約事項

### C-1: 技術スタック
- AWS CDK v2.120.0以上
- TypeScript 5.0以上
- Node.js 18以上

### C-2: リージョン
- 対象リージョン: ap-northeast-1（東京）

### C-3: 環境
- 開発環境（dev）と本番環境（prod）の2環境のみをサポート

## 受け入れ条件

### AC-1: プロジェクト構造
- [ ] `cdk/`ディレクトリが存在する
- [ ] `cdk/bin/app.ts`が存在する
- [ ] `cdk/lib/config/env-config.ts`が存在する
- [ ] `cdk/lib/config/dev.ts`が存在する
- [ ] `cdk/lib/config/prod.ts`が存在する
- [ ] `cdk/lib/stacks/`ディレクトリが存在する
- [ ] `cdk/lib/constructs/`ディレクトリが存在する

### AC-2: 設定ファイル
- [ ] `package.json`に必要な依存関係が定義されている
- [ ] `tsconfig.json`が適切に設定されている
- [ ] `cdk.json`が適切に設定されている

### AC-3: 環境設定
- [ ] `EnvConfig`型が定義されている
- [ ] 開発環境設定（dev.ts）が要件通りに定義されている
- [ ] 本番環境設定（prod.ts）が要件通りに定義されている
- [ ] `getEnvConfig`関数が環境名に応じて正しい設定を返す

### AC-4: ビルド確認
- [ ] `npm install`が正常に完了する
- [ ] `npm run build`（TypeScriptコンパイル）が正常に完了する
- [ ] `cdk synth`が正常に完了する（スタックが未実装でも構文エラーがないこと）

## 依存関係

### 前提条件
- フェーズ0（事前準備）が完了していること
  - CDK開発コンテナが起動していること
  - AWS認証情報が設定されていること
  - CDK Bootstrapが完了していること

### 後続フェーズへの影響
- フェーズ2（ネットワーク基盤）以降のすべてのスタック実装が本フェーズの成果物に依存する

## リスクと対策

### R-1: CDKバージョンの不整合
- **リスク**: package.jsonのバージョン指定が曖昧で、環境によって異なるバージョンがインストールされる
- **対策**: バージョンを明確に固定（^記号を使用し、メジャーバージョンのみ固定）

### R-2: 環境設定の誤り
- **リスク**: 環境設定の値が誤っていると、後続フェーズで問題が発生する
- **対策**: TypeScriptの型システムを活用し、必須パラメータの欠落を防ぐ

## 参考資料
- [AWS CDK公式ドキュメント](https://docs.aws.amazon.com/cdk/v2/guide/home.html)
- [implements_aws_by_cdk_plan.md](../../docs/architecture/implements_aws_by_cdk_plan.md) - フェーズ1セクション

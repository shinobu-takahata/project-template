# フェーズ1: CDK基盤セットアップ - タスクリスト

## 概要
AWS CDKプロジェクトの初期化と基本構造の構築に関するタスクを管理します。

## タスク一覧

### 1. ディレクトリ構造の作成
- [ ] **1.1** `cdk/`ディレクトリの作成
- [ ] **1.2** `cdk/bin/`ディレクトリの作成
- [ ] **1.3** `cdk/lib/`ディレクトリの作成
- [ ] **1.4** `cdk/lib/stacks/`ディレクトリの作成
- [ ] **1.5** `cdk/lib/constructs/`ディレクトリの作成
- [ ] **1.6** `cdk/lib/config/`ディレクトリの作成

**完了条件**: すべてのディレクトリが作成されていること

---

### 2. package.jsonの作成
- [ ] **2.1** `cdk/package.json`の作成
  - プロジェクト名: `cdk`
  - バージョン: `0.1.0`
  - bin設定: `"cdk": "bin/app.js"`
- [ ] **2.2** scripts設定の追加
  - `build`: `tsc`
  - `watch`: `tsc -w`
  - `test`: `jest`
  - `cdk`: `cdk`
- [ ] **2.3** dependencies設定の追加
  - `aws-cdk-lib`: `^2.120.0`
  - `constructs`: `^10.0.0`
  - `source-map-support`: `^0.5.21`
- [ ] **2.4** devDependencies設定の追加
  - `@types/jest`: `^29.5.0`
  - `@types/node`: `^20.0.0`
  - `jest`: `^29.5.0`
  - `ts-jest`: `^29.1.0`
  - `aws-cdk`: `^2.120.0`
  - `ts-node`: `^10.9.1`
  - `typescript`: `~5.3.0`

**完了条件**: package.jsonが正しく設定され、依存関係が定義されていること

---

### 3. tsconfig.jsonの作成
- [ ] **3.1** `cdk/tsconfig.json`の作成
- [ ] **3.2** compilerOptionsの設定
  - target: `ES2020`
  - module: `commonjs`
  - strict: `true`
  - esModuleInterop: `true`
  - declaration: `true`
  - inlineSourceMap: `true`
  - その他必要なオプション
- [ ] **3.3** exclude設定の追加
  - `node_modules`
  - `cdk.out`

**完了条件**: tsconfig.jsonが正しく設定されていること

---

### 4. cdk.jsonの作成
- [ ] **4.1** `cdk/cdk.json`の作成
- [ ] **4.2** app設定の追加
  - `"app": "npx ts-node --prefer-ts-exts bin/app.ts"`
- [ ] **4.3** watch設定の追加
  - includeとexcludeパターン
- [ ] **4.4** context設定の追加
  - CDK v2の最新feature flagsを有効化

**完了条件**: cdk.jsonが正しく設定されていること

---

### 5. 環境設定の実装

#### 5.1 env-config.ts（型定義と共通関数）
- [ ] **5.1.1** `cdk/lib/config/env-config.ts`の作成
- [ ] **5.1.2** `EnvConfig`インターフェースの定義
  - envName: 'dev' | 'prod'
  - region: string
  - vpcCidr: string
  - availabilityZones: string[]
  - publicSubnetCidrs: string[]
  - privateSubnetCidrs: string[]
  - useVpcEndpoints: boolean
  - ecs: { cpu, memory, desiredCount, minCapacity, maxCapacity }
  - aurora: { instanceClass, backupRetentionDays, deletionProtection }
  - logRetentionDays: number
  - domainName: string
- [ ] **5.1.3** `getEnvConfig`関数の実装
  - 引数: envName (string)
  - 返り値: EnvConfig
  - 環境名に応じて適切な設定を返す
  - 未知の環境名の場合はエラーをスロー

**完了条件**: env-config.tsが正しく実装されていること

#### 5.2 dev.ts（開発環境設定）
- [ ] **5.2.1** `cdk/lib/config/dev.ts`の作成
- [ ] **5.2.2** `devConfig`オブジェクトの定義
  - envName: 'dev'
  - region: 'ap-northeast-1'
  - vpcCidr: '10.0.0.0/16'
  - availabilityZones: ['ap-northeast-1a', 'ap-northeast-1c']
  - publicSubnetCidrs: ['10.0.1.0/24', '10.0.2.0/24']
  - privateSubnetCidrs: ['10.0.11.0/24', '10.0.12.0/24']
  - useVpcEndpoints: true
  - ecs: { cpu: 512, memory: 1024, desiredCount: 2, minCapacity: 2, maxCapacity: 10 }
  - aurora: { instanceClass: 'db.t4g.medium', backupRetentionDays: 7, deletionProtection: false }
  - logRetentionDays: 7
  - domainName: 'dev-api.example.com'
- [ ] **5.2.3** devConfigをexport

**完了条件**: dev.tsが正しく実装されていること

#### 5.3 prod.ts（本番環境設定）
- [ ] **5.3.1** `cdk/lib/config/prod.ts`の作成
- [ ] **5.3.2** `prodConfig`オブジェクトの定義
  - envName: 'prod'
  - region: 'ap-northeast-1'
  - vpcCidr: '10.1.0.0/16'
  - availabilityZones: ['ap-northeast-1a', 'ap-northeast-1c']
  - publicSubnetCidrs: ['10.1.1.0/24', '10.1.2.0/24']
  - privateSubnetCidrs: ['10.1.11.0/24', '10.1.12.0/24']
  - useVpcEndpoints: true
  - ecs: { cpu: 1024, memory: 2048, desiredCount: 2, minCapacity: 2, maxCapacity: 20 }
  - aurora: { instanceClass: 'db.r6g.large', backupRetentionDays: 30, deletionProtection: true }
  - logRetentionDays: 30
  - domainName: 'api.example.com'
- [ ] **5.3.3** prodConfigをexport

**完了条件**: prod.tsが正しく実装されていること

---

### 6. エントリーポイント（bin/app.ts）の実装
- [ ] **6.1** `cdk/bin/app.ts`の作成
- [ ] **6.2** shebang行の追加（`#!/usr/bin/env node`）
- [ ] **6.3** 必要なモジュールのインポート
  - `aws-cdk-lib`
  - `../lib/config/env-config`
- [ ] **6.4** CDKアプリケーションの初期化
  - `const app = new cdk.App();`
- [ ] **6.5** Context値から環境名を取得
  - `const envName = app.node.tryGetContext('env') || 'dev';`
- [ ] **6.6** 環境設定の読み込み
  - `const config = getEnvConfig(envName);`
- [ ] **6.7** AWS環境設定の定義
  - account: `process.env.CDK_DEFAULT_ACCOUNT`
  - region: `config.region`
- [ ] **6.8** app.synth()の呼び出し

**完了条件**: bin/app.tsが正しく実装されていること

---

### 7. 依存関係のインストール
- [ ] **7.1** CDK開発コンテナに入る
  ```bash
  docker-compose exec cdk bash
  ```
- [ ] **7.2** cdkディレクトリに移動
  ```bash
  cd /workspace/cdk
  ```
- [ ] **7.3** npm installの実行
  ```bash
  npm install
  ```
- [ ] **7.4** インストール成功の確認
  - node_modulesディレクトリが作成されていること
  - package-lock.jsonが作成されていること
  - エラーが出ていないこと

**完了条件**: すべての依存関係が正常にインストールされていること

---

### 8. ビルドと検証

#### 8.1 TypeScriptコンパイル
- [ ] **8.1.1** npm run buildの実行
  ```bash
  npm run build
  ```
- [ ] **8.1.2** コンパイル成功の確認
  - `bin/app.js`が生成されていること
  - `lib/config/env-config.js`が生成されていること
  - `lib/config/dev.js`が生成されていること
  - `lib/config/prod.js`が生成されていること
  - エラーが出ていないこと

**完了条件**: TypeScriptのコンパイルが正常に完了すること

#### 8.2 CDK合成テスト（dev環境）
- [ ] **8.2.1** AWS_PROFILEとAWS_REGIONを設定
  ```bash
  export AWS_PROFILE=your-profile-name
  export AWS_REGION=ap-northeast-1
  ```
- [ ] **8.2.2** cdk synthの実行（dev環境）
  ```bash
  cdk synth --context env=dev
  ```
- [ ] **8.2.3** 合成成功の確認
  - cdk.outディレクトリが作成されていること
  - エラーが出ていないこと
  - 警告が出ていないこと（スタックが未実装なので空の合成結果でOK）

**完了条件**: dev環境でのCDK合成が正常に完了すること

#### 8.3 CDK合成テスト（prod環境）
- [ ] **8.3.1** cdk synthの実行（prod環境）
  ```bash
  cdk synth --context env=prod
  ```
- [ ] **8.3.2** 合成成功の確認
  - cdk.outディレクトリが更新されていること
  - エラーが出ていないこと
  - 警告が出ていないこと

**完了条件**: prod環境でのCDK合成が正常に完了すること

---

### 9. ドキュメントの作成（任意）
- [ ] **9.1** `cdk/README.md`の作成
  - プロジェクト概要
  - ディレクトリ構造の説明
  - 環境設定の説明
  - デプロイ手順
  - トラブルシューティング

**完了条件**: README.mdが作成されていること（任意）

---

### 10. .gitignoreの更新
- [ ] **10.1** `cdk/.gitignore`の確認・更新
  - node_modules
  - cdk.out
  - *.js
  - *.d.ts
  - !jest.config.js
  - package-lock.json（オプション）

**完了条件**: .gitignoreが適切に設定されていること

---

## 全体の完了条件

以下のすべてが満たされていること：
- [ ] ディレクトリ構造が正しく作成されている
- [ ] package.json、tsconfig.json、cdk.jsonが正しく設定されている
- [ ] 環境設定ファイル（env-config.ts、dev.ts、prod.ts）が実装されている
- [ ] エントリーポイント（bin/app.ts）が実装されている
- [ ] npm installが正常に完了している
- [ ] TypeScriptのコンパイルが正常に完了している
- [ ] dev環境とprod環境でのCDK合成が正常に完了している

## トラブルシューティング

### npm installが失敗する場合
1. Node.jsバージョンを確認（v18以上）
2. npmキャッシュをクリア（`npm cache clean --force`）
3. package.jsonの依存関係を確認

### TypeScriptコンパイルエラーが出る場合
1. tsconfig.jsonの設定を確認
2. 型定義ファイル（@types/*）がインストールされているか確認
3. エラーメッセージを詳細に確認し、コードを修正

### cdk synthが失敗する場合
1. AWS認証情報が正しく設定されているか確認
2. cdk.jsonのapp設定が正しいか確認
3. bin/app.tsのsyntaxエラーがないか確認

### Context値が反映されない場合
1. --context env=<環境名>を正しく指定しているか確認
2. getEnvConfig関数が正しく実装されているか確認
3. cdk.out/を削除して再度合成を試す

## 次のステップ
すべてのタスクが完了したら、フェーズ2（ネットワーク基盤）に進みます。

フェーズ2では以下を実装します：
- NetworkStack（VPC、サブネット、VPCエンドポイント、Route53）
- multi-az-vpc Construct

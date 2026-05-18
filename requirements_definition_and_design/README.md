# 要件定義・設計ドキュメント

プロジェクトの要件定義から設計までの成果物を格納するディレクトリです。

---

## ディレクトリ構造

```
requirements_definition_and_design/
├── project_plan/               # プロジェクト計画
│   ├── kickoff.md
│   ├── project_plan.md
│   ├── project_plan.pdf
│   └── rd_plan/
│       └── rd_plan.md
├── non_functional/             # 非機能要件
│   ├── 1-セキュリティ.md
│   ├── 2-可用性.md
│   ├── 3-性能・拡張性.md
│   └── 4-運用・保守性.md
└── requirements_definition/    # 要件定義・設計
    ├── workflow.drawio         # 業務フロー（draw.io）
    ├── workflow.svg            # 業務フロー（SVG）
    ├── work_picture.drawio     # 業務全体像
    ├── based_design/           # 基本設計
    │   ├── api-design-template.md
    │   ├── data-model-template.md
    │   ├── db-table-definition-template.md
    │   ├── domain_logic_design_process.md # ドメインモデルを作成するための指針となるドキュメント    
    │   ├── role-permission-template.md
    │   └── ui/
    │       ├── ui.dio                          # 画面設計（draw.io）
    │       ├── ui.svg                          # 画面設計（SVG）
    │       └── screen-item-definition-template.md
    ├── detailed_design/        # 詳細設計
    │   ├── backend/
    │   │   ├── README.md
    │   │   └── detailed_design_template.md
    │   └── frontend/
    │       └── README.md
    ├── quality/                # 品質基準
    │   ├── quality.md
    │   ├── functioinal_suitability.md
    │   └── performance_efficiency.md
    └── test/                   # テスト計画・管理
        ├── test_plan.md
        ├── test_content.md
        └── test_management.md
```

---

## ドキュメントの種類

### project_plan/ — プロジェクト計画

プロジェクト全体の進め方を定義します。

| ファイル | 内容 |
|---|---|
| `kickoff.md` | キックオフの議事録・合意事項 |
| `project_plan.md` | プロジェクト計画書（スコープ・スケジュール・体制・コスト・リスク管理等） |
| `rd_plan/rd_plan.md` | 要件定義フェーズの作業計画 |

### non_functional/ — 非機能要件

機能要件とは独立したシステム品質の要件を定義します。

| ファイル | 内容 |
|---|---|
| `1-セキュリティ.md` | 認証・認可・データ保護・脆弱性対策 |
| `2-可用性.md` | 稼働率・障害復旧・SLA |
| `3-性能・拡張性.md` | 応答時間・スループット・スケーリング |
| `4-運用・保守性.md` | 監視・ログ・デプロイ・保守運用 |

### requirements_definition/ — 要件定義・設計

要件定義から詳細設計までの成果物を格納します。

#### 業務フロー

| ファイル | 内容 |
|---|---|
| `workflow.drawio / .svg` | 業務フロー図（現状フロー・To-Beフロー） |
| `work_picture.drawio` | 業務全体像・コンテキスト図 |

#### based_design/ — 基本設計

システムの骨格となる設計を定義します。各ファイルはテンプレートとして用意されており、プロジェクトに応じて記述します。

| ファイル | 内容 |
|---|---|
| `api-design-template.md` | REST APIエンドポイント一覧・リクエスト/レスポンス定義の雛形 |
| `data-model-template.md` | ドメインモデル・エンティティ関係の定義の雛形 |
| `db-table-definition-template.md` | DBテーブル定義・カラム・インデックスの雛形 |
| `role-permission-template.md` | ロール・権限マトリクスの雛形 |
| `ui/ui.dio / .svg` | 画面遷移図・ワイヤーフレームの雛形 |
| `ui/screen-item-definition-template.md` | 画面項目定義書の雛形（各画面の入出力項目・バリデーション） |

#### detailed_design/ — 詳細設計

基本設計をもとに、実装レベルの詳細設計を記述します。

| ディレクトリ | 内容 |
|---|---|
| `backend/` | APIエンドポイントごとの処理フロー・ユースケース詳細設計 |
| `frontend/` | 画面コンポーネントごとの実装仕様 |

各ディレクトリのREADMEに、詳細設計書の作成方法と Claude Code への渡し方が記載されています。

#### quality/ — 品質基準

ISO/IEC 25010 に基づく品質特性の定義と評価基準を記載します。

| ファイル | 内容 |
|---|---|
| `quality.md` | 品質特性の全体定義（ISO/IEC 25010） |
| `functioinal_suitability.md` | 機能適合性の評価基準・メトリクス |
| `performance_efficiency.md` | 性能効率性の評価基準・メトリクス |

#### test/ — テスト計画・管理

| ファイル | 内容 |
|---|---|
| `test_plan.md` | テスト戦略・スコープ・スケジュール |
| `test_content.md` | テストケース・テスト観点 |
| `test_management.md` | テスト進捗管理・バグトラッキング方針 |

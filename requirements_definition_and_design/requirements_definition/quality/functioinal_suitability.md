# 機能適合性

GitHub ProjectsとAWSを使っている環境であれば、**「データの自動収集」と「可視化」**が非常にやりやすい構成です。

JIS X 25023の指標を、具体的にどうGitHubとAWSから抽出して「機能適合性」を測定するか、その実装イメージを提案します。

---

## 1. 機能網羅性 (Functional Completeness) の出し方

GitHub Projectsの**「Issue/Taskのステータス」**をデータソースにします。

* **使用するデータ:**
* **B (全体):** プロジェクトのバックログにある全Issue数（`label:feature` などでフィルタ）。
* **A (不足):** 期限までに `status:Done` にならなかったIssue数、または `label:wontfix` になった数。


* **GitHubでのやり方:**
* **Insights機能:** GitHub Projectsの「Insights」タブで、ステータス別の積み上げグラフを表示。
* **自動計算:** GitHub API（GraphQL）を使って、「全体のIssue数」と「ClosedされたIssue数」を取得し、算出します。
* **指標の意味:** 「予定していた機能のうち、どれだけリリースに載せられたか」を可視化します。



## 2. 機能正確性 (Functional Correctness) の出し方

GitHubの**「バグ報告Issue」**とAWS上の**「テスト結果」**をデータソースにします。

* **使用するデータ:**
* **B (全体):** 実施したテストケースの総数（GitHub Actions上のテストログ）。
* **A (不正確):** テスト失敗数、または `label:bug` かつ `label:functional` で起票されたIssue数。


* **やり方の具体例:**
* **GitHub Actions:** CIを実行した際に出力される `junit.xml` などのテスト結果ファイルから、Total（B）とFailures（A）を抽出。
* **GitHub Issues:** 本番（またはステージング）で見つかった「期待した動作と違う」というバグIssueの件数をカウント。


* **数式の当てはめ:** `1 - (Bug数 / テストケース総数)`。

## 3. 機能適切性 (Functional Appropriateness) の出し方

AWS上の**「ユーザー行動ログ」**をデータソースにします。

* **使用するデータ:**
* **B (全体):** 特定のタスク（例：購入、会員登録）を開始したユーザー数。
* **A (適切):** そのタスクを最後まで完了（コンバージョン）したユーザー数。


* **AWSでのやり方:**
* **Amazon CloudWatch RUM (Real User Monitoring):** ユーザーがブラウザ上でどのボタンを押し、どこで離脱したかを追跡します。
* **AWS Pinpoint:** ユーザーのジャーニー（行程）を分析し、機能がユーザーの目的に対して「適切」に機能している（＝離脱せずに目的を達成している）かを測定します。


* **指標の意味:** 「機能は存在するが、使いにくくて目的が達成できない」場合、この数値が下がります。

---

## 実践的な構成案：品質ダッシュボードの構築

GitHubとAWSのデータを組み合わせて、JIS X 25023の数値を自動更新する仕組みを作ると管理が楽になります。

1. **データ集約:**
* **GitHub Actions** からテスト成功率を **Amazon CloudWatch Metrics** に送信。
* **GitHub API** からIssueの消化率を定期的に取得（AWS Lambda等を使用）。


2. **可視化:**
* **Amazon Managed Grafana** または **CloudWatch Dashboards** を使い、以下のようなグラフを作成。
* 「機能網羅率（GitHubのDone率）」
* 「機能正確性（テスト成功率）」
* 「残存バグ密度（Issue数 / コード行数）」





---

### 次のステップへの提案

まずは一番手軽な**「GitHub Actionsのテスト結果（正確性）」**か、**「GitHub ProjectsのIssue消化率（網羅性）」**を数値化してみるのがおすすめです。

**もしよろしければ、GitHub Actionsでテスト結果を集計してCloudWatchに送るような具体的なスクリプト例や、GitHub APIでIssue数を数えるクエリ例を紹介しましょうか？**
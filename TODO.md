TODO

- awsの構築の手順をざっくりドキュメントにする
- awsの構成要素を見直す

- ecs用のdockefileを用意する
  - proxy-headerの記述
  - --reloadの削除
  - その他何か必要だった気がする（worker）

- devcontainerについて
  - overrideCommandはこれでいい。
  - cmdを上書きして停止
  - コンテナ内でdebuggerを起動
  - ただ、dockerfileと差分が出てしまうのが困るため、その検証は何らかのタイミングで行う必要がある（インテグレーションテストかな？）
  - dockerdesktopどうするか

- 社内の研修用の環境のために
  - どういうルールを強制するか
  - ガバナンス設計をしておく必要あり
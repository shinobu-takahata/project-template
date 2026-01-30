## Claude Codeについて
適当に使っていると、すぐにコンテキストウィンドウがいっぱいになる。

そのため、適宜コンテキストをclearする必要がある。
- /clear
- /compact

また、そうすると、情報を適切に保持できなくなるため、steeringファイルや、skillに情報を切り出しておく

何度もClaude Codeにお願いしているような内容はskillに切り出しておく


## Backend
/README/README_backend.mdを参照

## エディタ
Github CodeSpacesを使用している場合、デフォルトの設定だと、拡張機能を入れてもセマンティックハイライトが効かないです。
そのため、settings.jsonに以下を加える必要があります。
（エディタのカラーテーマを特定のものにする必要があります。）
```
"workbench.colorTheme": "Default Dark Modern",
```
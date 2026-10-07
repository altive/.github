# .github

## .github/workflows

別リポジトリから共通で呼び出して使いたいworkflowファイルを配置するディレクトリです。

当リポジトリはPublicリポジトリなので、別Organizationからでも利用可能です。

https://docs.github.com/en/actions/using-workflows/reusing-workflows

### create-release-pull-request-for-flutter-app.yaml
Flutter/Dart の `pubspec.yaml` 内のバージョンとビルドを書き換えて、Pull requestを作成するworkflowです。

`build-number` には、増分ではなく更新後のビルド番号を文字列で指定できます。
省略または空文字の場合は、現在のビルド番号に1を加算します。
指定する場合は、`pubspec.yaml` の現在値より大きい正の整数が必要です。
不正な値は、ブランチ作成やpushを行う前にエラーになります。
`version` を省略すると、現在のバージョンを維持します。

```yaml
with:
  version: "2.76.1"
  build-number: "502"
  working-directory: "./packages/flutter_app"
```

この例は、対象の `pubspec.yaml` の現在のビルド番号が502未満の場合に使用できます。
既存の呼び出し元は変更不要です。`branch-path-segment` によるブランチ名の指定も引き続き利用できます。

番号決定・入力検証のテストは `python3 -m unittest discover -s tests -v`、
ワークフローの静的検証は `actionlint` で実行できます。

## workflow-template

Organization内でテンプレートとして使いたいworkflow雛形ファイルを配置するディレクトリです。

https://docs.github.com/en/actions/using-workflows/creating-starter-workflows-for-your-organization

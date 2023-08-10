# .github

## .github/workflows

別リポジトリから共通で呼び出して使いたいworkflowファイルを配置するディレクトリです。

当リポジトリはPublicリポジトリなので、別Organizationからでも利用可能です。

https://docs.github.com/en/actions/using-workflows/reusing-workflows

### create-release-pull-request-for-flutter-app.yaml
Flutter/Dart の `pubspec.yaml` 内のバージョンとビルドを書き換えて、Pull requestを作成するworkflowです。

## workflow-template

Organization内でテンプレートとして使いたいworkflow雛形ファイルを配置するディレクトリです。

https://docs.github.com/en/actions/using-workflows/creating-starter-workflows-for-your-organization
---
name: 機能フラグ追加
about: 機能フラグ追加用のテンプレート
title: "〇〇機能フラグを追加する"
labels:
assignees: ""
---

```[tasklist]
### Tasks
- [ ] 機能フラグ`xxx_feature_enabled`を使用したコードを追加する。
- [ ] 検証環境のRemoteConfigのパラメータを追加する。
- [ ] 本番環境のRemoteConfigのパラメータを追加する。
```

> [!NOTE]
> 機能フラグを追加した場合は、「機能フラグで追加したコードの削除」と「機能フラグで設定した RemoteConfigパラメータの削除」用の Issue も起票してください。
> また、実装コードに TODO コメントと、起票した削除用のIssue URL を追加してください。

```[tasklist]
### 関連Issue起票
- [ ] 〇〇用機能フラグの実装コード削除とパラメータアーカイブ
```

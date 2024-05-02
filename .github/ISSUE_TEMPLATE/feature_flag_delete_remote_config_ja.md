---
name: 機能フラグで設定したRemoteConfig削除
about: 機能フラグで設定したRemoteConfig削除用のテンプレート
title: "〇〇機能フラグで設定したRemoteConfigを削除する"
labels: refactor
assignees: ""
---

```[tasklist]
### RemoteConfig削除
- [ ] 検証環境のパラメータを削除する。
- [ ] 本番環境のパラメータを削除する。
```

> [!WARNING]
> 以下の手順を実施済みかどうか確認してください。
>
> 1. 機能フラグを使用したコードを削除する。
> 2. 削除を行ったバージョンをリリースする。
> 3. 削除を行ったバージョンへ強制アップデートする。

# リマインダー仕様

## AQUAフィルター掃除リマインダー

- **ワークフローファイル**: `.github/workflows/post-remind-to-discord-clean-aqua-filter.yml`
- **送信先**: Discord (Webhook)
- **メッセージ形式**: `🐥 < AQUAのフィルター掃除をするﾋﾟﾖ！ <担当> @everyone`
- **担当選択ロジック**: 実行時に `担当はY！` および `担当はH！` からランダム（`$RANDOM` を使用）で1つが選ばれます。

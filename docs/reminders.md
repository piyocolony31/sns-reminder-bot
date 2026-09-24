# リマインダー仕様

## AQUAフィルター掃除リマインダー

- **ワークフローファイル**: `.github/workflows/post-remind-to-discord-clean-aqua-filter.yml`
- **送信先**: Discord (Webhook)
- **メッセージ形式**: `🐥 < AQUAのフィルター掃除をするﾋﾟﾖ！ <担当> @everyone`
- **担当選択ロジック**: 実行時に `担当はY！` および `担当はH！` からランダム（`$RANDOM` を使用）で1つが選ばれます。

## 秀峰閣 湖月 キャンセル待ち（空室チェック）通知

- **ワークフローファイル**: `.github/workflows/check-kogetsu-vacancy.yml`
- **スクリプト**: `check-kogetsu-vacancy/main.py`
- **送信先**: Discord (Webhook)
- **チェック対象条件**:
  - 対象ホテル: 秀峰閣 湖月 (ホテルコード `0000001834`)
  - 人数: 大人3名 (`lt001=0_1_2_3_4_6`, `lnum001=3_0_0_0_0_0`)
  - 宿泊期間: 1泊 (`stays=1`)
  - 対象期間: 2026年12月1日 〜 2027年3月31日の日曜日チェックイン
  - 除外日: 1月3日 (2027年1月3日など) は通知スキップ対象
- **実行周期**: 毎時15分 (cron: `15 * * * *`) および `workflow_dispatch` (手動実行)


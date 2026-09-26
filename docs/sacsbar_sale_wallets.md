# Sacs Bar セール長財布 監視・通知システム仕様書

## 概要
Sacs Bar (サックスバー) 公式サイトのメンズ・ユニセックスセールページ (`https://sacsbar.com/c/sale/sale_mens_uni_sex?page=1&sort=latest`) を自動巡回し、在庫ありの「長財布」カテゴリ商品を抽出します。前回実行時と比較して新着商品が追加されていた場合、Discord や LINE に自動通知します。

## 仕様

### 1. クロール & 早期打ち切りロジック
- **言語設定**: `ja-JP`（日本語表示で判定）
- **ページ巡回**: `page=1` から順に `sort=latest` でアクセス。
- **在庫切れ判定**: 商品カードのテキスト・要素に「在庫切れ」「在庫なし」「SOLD OUT」「out of stock」「完売」が含まれるか判定。
- **打ち切り条件**: 商品一覧は新着順に並んでおり後半は在庫切れ商品となるため、**「在庫切れ」の商品を1つでも検出した時点でそれ以降の全ページのクロールを即時停止**します。

### 2. カテゴリ抽出条件
商品名・テキストに以下のキーワードのいずれかが含まれる商品を長財布として抽出します。
- `長財布`
- `ロングウォレット`
- `long wallet`
- `ラウンドファスナー`
- `ラウンド長財布`
- `かぶせ長財布`
- `L字ファスナー長財布`

### 3. 状態保持・差分検知
- 検出された長財布データは [known_wallets.json](../check-sacsbar-sale-wallets/known_wallets.json) に保存します。
- 次回実行時に保存済みの商品IDと比較し、未検知の商品IDが存在する場合のみ「新着アイテム」として通知を行います。

### 4. 通知機能
- `DISCORD_WEBHOOK_AUTOCHECK_URL` を使用して Discord Webhook へ通知を送信します。

### 5. GitHub Actions 自動化
[check-sacsbar-sale-wallets.yml](../.github/workflows/check-sacsbar-sale-wallets.yml)
- 毎日日本時間9:00（`0 0 * * *`）に自動実行および手動実行（`workflow_dispatch`）
- 実行後、`known_wallets.json` に変更があった場合は自動的にコミット＆プッシュされます。

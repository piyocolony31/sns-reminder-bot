import asyncio
import json
import logging
import os
import sys
import urllib.parse
import urllib.request
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "known_wallets.json")

# Discord Webhook 通知用環境変数
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_AUTOCHECK_URL")

# 長財布判定用キーワード
LONG_WALLET_KEYWORDS = [
    "長財布",
    "ロングウォレット",
    "long wallet",
    "ラウンドファスナー",
    "ラウンド長財布",
    "かぶせ長財布",
    "L字ファスナー長財布",
]


def send_http_post(url: str, headers: dict, data_bytes: bytes, timeout: int = 10):
    """urllibを使用した汎用HTTP POSTリクエスト"""
    req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status


def notify_discord(message_text: str) -> bool:
    """Discord Webhook を使用して通知"""
    if not DISCORD_WEBHOOK_URL:
        logging.info("DISCORD_WEBHOOK_AUTOCHECK_URL が設定されていないため、Discord通知をスキップします。")
        return False

    headers = {"Content-Type": "application/json"}
    payload = {"content": message_text}

    try:
        data_bytes = json.dumps(payload).encode("utf-8")
        status = send_http_post(DISCORD_WEBHOOK_URL, headers, data_bytes)
        logging.info(f"Discord通知を送信しました (status: {status})。")
        return True
    except Exception as e:
        logging.error(f"Discord通知送信エラー: {e}")
        return False
        logging.info("LINE_CHANNEL_ACCESS_TOKEN または LINE_GROUP_ID が設定されていないため、LINE通知をスキップします。")
        return False

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
    }
    payload = {
        "to": LINE_GROUP_ID,
        "messages": [{"type": "text", "text": message_text}],
    }

    try:
        data_bytes = json.dumps(payload).encode("utf-8")
        status = send_http_post(url, headers, data_bytes)
        logging.info(f"LINE通知を送信しました (status: {status})。")
        return True
    except Exception as e:
        logging.error(f"LINE通知送信エラー: {e}")
        return False


def is_long_wallet(text: str) -> bool:
    """テキストが長財布カテゴリに合致するかどうか判定"""
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in LONG_WALLET_KEYWORDS)


def extract_product_id(link: str) -> str:
    """URLから商品識別IDを抽出"""
    if not link:
        return ""
    path = link.rstrip("/").split("?")[0]
    return path.split("/")[-1]


async def crawl_sacsbar_sale_wallets():
    """
    Sacs Bar のセールページを巡回し、在庫ありの長財布を抽出。
    在庫切れ商品が出現した時点でそれ以降のクロールを即時ストップ。
    """
    wallets = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="ja-JP",
            extra_http_headers={"Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7"}
        )
        page = await context.new_page()

        current_page = 1
        stopped_by_sold_out = False

        while True:
            url = f"https://sacsbar.com/c/sale/sale_mens_uni_sex?page={current_page}&sort=latest"
            logging.info(f"Fetching page {current_page}: {url}")
            await page.goto(url, wait_until="networkidle")

            page_data = await page.evaluate('''() => {
                const productNodes = document.querySelectorAll('.fs-c-productListItem');
                const result = [];

                productNodes.forEach(node => {
                    const text = node.innerText || '';
                    const linkEl = node.querySelector('a[href*="/c/"]') || node.querySelector('a');
                    const link = linkEl ? linkEl.href : '';

                    const isSoldOut = text.includes('在庫切れ') || 
                                      text.includes('在庫なし') || 
                                      text.includes('SOLD OUT') || 
                                      text.includes('out of stock') || 
                                      text.includes('完売') ||
                                      !!node.querySelector('.fs-c-productListItem__soldout, [class*="soldout"]');

                    result.push({ link, text, isSoldOut });
                });

                const paginationItems = Array.from(document.querySelectorAll('.fs-c-pagination__item'));
                const pageNums = paginationItems
                    .map(el => parseInt(el.innerText.trim(), 10))
                    .filter(n => !isNaN(n));
                const maxPage = pageNums.length > 0 ? Math.max(...pageNums) : 1;

                return { items: result, maxPage };
            }''')

            items = page_data['items']
            max_page = page_data['maxPage']

            if not items:
                logging.info(f"Page {current_page} に商品が見つかりませんでした。クロールを終了します。")
                break

            for idx, item in enumerate(items):
                # 在庫切れが含まれる場合、以降のクロールを全て打ち切り
                if item['isSoldOut']:
                    logging.info(f"Page {current_page} の {idx + 1} 件目で在庫切れ商品を検出したためクロールを即時終了します。")
                    stopped_by_sold_out = True
                    break

                if is_long_wallet(item['text']):
                    product_id = extract_product_id(item['link'])
                    clean_text = " | ".join([line.strip() for line in item['text'].split("\n") if line.strip()])
                    wallets.append({
                        "id": product_id,
                        "link": item['link'],
                        "title": clean_text
                    })

            if stopped_by_sold_out or current_page >= max_page:
                if current_page >= max_page and not stopped_by_sold_out:
                    logging.info(f"最大ページ数 ({max_page}) に達したためクロールを終了します。")
                break

            current_page += 1

        await browser.close()

    return wallets


def load_known_wallets() -> list:
    """前回保存された既知の長財布データを読み込み"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"{DATA_FILE} の読み込みエラー: {e}")
    return []


def save_known_wallets(wallets: list):
    """抽出された長財布データを保存"""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(wallets, f, ensure_ascii=False, indent=2)
        logging.info(f"{DATA_FILE} に {len(wallets)} 件のデータを保存しました。")
    except Exception as e:
        logging.error(f"{DATA_FILE} の保存エラー: {e}")


def format_notification_message(new_items: list) -> str:
    """新着商品の通知メッセージ作成"""
    lines = [
        "👜【Sacs Bar セール】新着の長財布が追加されました！",
        f"全 {len(new_items)} 件の新着アイテムがあります。",
        "",
    ]
    for item in new_items:
        lines.append(f"・{item['title']}")
        lines.append(f"  🔗 {item['link']}")
        lines.append("")
    return "\n".join(lines).strip()


def main():
    logging.info("=== Sacs Bar セール長財布チェッカー開始 ===")

    current_wallets = asyncio.run(crawl_sacsbar_sale_wallets())
    logging.info(f"今回のクロールで検出した在庫あり長財布: {len(current_wallets)}件")

    known_wallets = load_known_wallets()
    known_ids = {item["id"] for item in known_wallets if "id" in item}

    # 新着商品の抽出
    new_items = [item for item in current_wallets if item["id"] not in known_ids]

    if new_items:
        logging.info(f"新着長財布を {len(new_items)} 件検出しました！")
        msg = format_notification_message(new_items)
        logging.info(f"\n--- 通知メッセージ ---\n{msg}\n---------------------")

        # Discord 通知
        sent_discord = notify_discord(msg)
        if not sent_discord:
            logging.info("通知先のWebhookが未設定、または送信に失敗しました。")
    else:
        logging.info("新着の長財布はありませんでした。")

    # 最新状態を保存
    save_known_wallets(current_wallets)


if __name__ == "__main__":
    main()

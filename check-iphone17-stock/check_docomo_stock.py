import os
import sys
import time
import requests
from playwright.sync_api import sync_playwright, TimeoutError

URL = (
    "https://www.docomo.ne.jp/product/onlineshop-ap/?mg_name=iPhone%2017"
    "&mg_capa=256GB&mg_procedure=%E6%A9%9F%E7%A8%AE%E6%9B%B4"
    "&icid=CRP_IPH_17_charge_top_to_CRP_PRD_onlineshop-ap#js-mg_products_area"
)
AVAILABLE_TEXT = "予約可能"


def send_discord(webhook_url: str, message: str, screenshot_path: str = None):
    """Send a Discord notification, optionally with a screenshot."""
    if not webhook_url:
        print("No Discord webhook set; skipping send")
        return

    try:
        data = {"content": message}
        files = {"file": open(screenshot_path, "rb")} if screenshot_path else None
        resp = requests.post(webhook_url, data=data, files=files, timeout=15)
        resp.raise_for_status()
        print("Discord webhook posted")
    except Exception as e:
        print(f"Failed to post webhook: {e}")
    finally:
        if files:
            files["file"].close()


def main():
    webhook = os.environ.get("DISCORD_WEBHOOK_AUTOCHECK_URL") or os.environ.get("DISCORD_WEBHOOK_URL")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            print(f"Opening {URL}")
            page.goto(URL, timeout=60000)
        except TimeoutError:
            print("Timeout while loading page or waiting for available text")
            screenshot_path = "/tmp/docomo_error.png"
            page.screenshot(path=screenshot_path, full_page=True)
            send_discord(webhook, "Error: Timeout occurred", screenshot_path)
            browser.close()
            sys.exit(2)
        
        time.sleep(10)

        try:
            count = page.locator(f"text={AVAILABLE_TEXT}").count()
        except Exception:
            count = 0

        print(f"Found '{AVAILABLE_TEXT}' {count} times.")

        if count != 53: # DOMは53個。見た目上は5個。
            msg = f"[docomoチェック] 在庫状況に変化あり: '{AVAILABLE_TEXT}' が {count} 個あります。\n{URL}"
            print("Sending webhook", msg)
            screenshot_path = "/tmp/docomo_stock_change.png"
            page.screenshot(path=screenshot_path, full_page=True)
            send_discord(webhook, msg, screenshot_path)
        else:
            print("Stock status is as expected (5 items available).")

        browser.close()


if __name__ == "__main__":
    main()

import os
import sys
import time
import requests
from playwright.sync_api import sync_playwright, TimeoutError

URL = "https://akizukidenshi.com/catalog/g/g129607/"
IN_STOCK_TEXT_1 = "かごに入れる"

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
            print("Timeout while loading page")
            screenshot_path = "/tmp/akizuki_error.png"
            page.screenshot(path=screenshot_path, full_page=True)
            send_discord(webhook, "Error: Timeout occurred while checking Akizuki stock", screenshot_path)
            browser.close()
            sys.exit(2)
        
        time.sleep(5)

        try:
            cart_btns = page.locator(".block-goods-detail-cart-btns")
            if cart_btns.count() > 0:
                text = cart_btns.first.inner_text()
                has_cart_button = IN_STOCK_TEXT_1 in text
            else:
                has_cart_button = False
        except Exception as e:
            print(f"Error extracting stock info: {e}")
            has_cart_button = False

        print(f"has_cart_button: {has_cart_button}")

        # If the 'かごに入れる' (add to cart) button is present, it can be purchased.
        if has_cart_button:
            msg = f"[秋月電子チェック] Raspberry Pi Zero 2 WH(完成品) の在庫が復活した可能性があります！\n{URL}"
            print("Sending webhook", msg)
            screenshot_path = "/tmp/akizuki_stock.png"
            page.screenshot(path=screenshot_path, full_page=True)
            send_discord(webhook, msg, screenshot_path)
        else:
            print("Stock is not available yet.")

        browser.close()


if __name__ == "__main__":
    main()

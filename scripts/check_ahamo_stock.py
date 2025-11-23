#!/usr/bin/env python3
"""
Check stock availability on ahamo product page using Playwright.

For each color radio button (Japanese names), click it and check whether
the text "この端末は在庫切れのため、" appears. If the text is NOT present,
post a message to the Discord webhook specified by the
`DISCORD_WEBHOOK_AUTOCHECK_URL` environment variable (preferred).

Run locally like:
    DISCORD_WEBHOOK_AUTOCHECK_URL=https://... python scripts/check_ahamo_stock.py

"""
import os
import sys
import time
import requests
from playwright.sync_api import sync_playwright, TimeoutError

URL = (
    "https://ahamo.com/store/pub/application/contract/"
    "?reuse=0&useType=0&orderDiv=03&representModelCode=004MD&modelCode=004MD"
)

COLORS = ["ラベンダー", "ホワイト", "ブラック", "ミストブルー", "セージ"]
OUT_OF_STOCK_TEXT = "この端末は在庫切れのため、"


def send_discord(webhook_url: str, message: str):
    if not webhook_url:
        print("No Discord webhook environment variable set (DISCORD_WEBHOOK_AUTOCHECK_URL or DISCORD_WEBHOOK_URL); skipping send")
        return
    try:
        resp = requests.post(webhook_url, json={"content": message}, timeout=15)
        resp.raise_for_status()
        print("Discord webhook posted")
    except Exception as e:
        print(f"Failed to post webhook: {e}")


def try_click_color(page, color: str) -> bool:
    """Try several strategies to click the color radio/button. Return True if clicked."""
    # Strategy 1: role=radio with name
    try:
        radios = page.get_by_role("radio", name=color)
        if radios.count() > 0:
            radios.first.click()
            return True
    except Exception:
        pass

    # Strategy 2: label that contains the text
    try:
        lbl = page.locator(f"label:has-text('{color}')")
        if lbl.count() > 0:
            lbl.first.click()
            return True
    except Exception:
        pass

    # Strategy 3: any element with exact text (button/span)
    try:
        elem = page.locator(f"text=^{color}$")
        if elem.count() > 0:
            elem.first.click()
            return True
    except Exception:
        pass

    # Strategy 4: partial text
    try:
        elem = page.locator(f"text={color}")
        if elem.count() > 0:
            elem.first.click()
            return True
    except Exception:
        pass

    return False


def try_click_option(page, option: str) -> bool:
    """Generic clicker for options like storage sizes (e.g. '256', '512')."""
    # Try role=radio first
    try:
        radios = page.get_by_role("radio", name=option)
        if radios.count() > 0:
            radios.first.click()
            return True
    except Exception:
        pass

    # label that contains the text
    try:
        lbl = page.locator(f"label:has-text('{option}')")
        if lbl.count() > 0:
            lbl.first.click()
            return True
    except Exception:
        pass

    # exact text node
    try:
        elem = page.locator(f"text=^{option}$")
        if elem.count() > 0:
            elem.first.click()
            return True
    except Exception:
        pass

    # partial text
    try:
        elem = page.locator(f"text={option}")
        if elem.count() > 0:
            elem.first.click()
            return True
    except Exception:
        pass

    return False


def main():
    # Prefer channel-specific secret name; fall back to the generic one if present.
    webhook = os.environ.get("DISCORD_WEBHOOK_AUTOCHECK_URL") or os.environ.get("DISCORD_WEBHOOK_URL")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print(f"Opening {URL}")
        try:
            page.goto(URL, timeout=60000)
        except TimeoutError:
            print("Timeout while loading page")
            browser.close()
            sys.exit(2)

        # small wait for dynamic content
        time.sleep(2)

        # Before selecting colors, explicitly select the 256GB storage option
        # (there is also 512, so choose 256 to make selection explicit)
        size_candidates = ["256", "256GB", "256 GB", "256ギガ", "256G"]
        size_selected = False
        for s in size_candidates:
            try:
                if try_click_option(page, s):
                    print(f"Selected storage option: {s}")
                    size_selected = True
                    # allow page to update
                    time.sleep(1)
                    break
            except Exception as e:
                print(f"Error selecting storage option '{s}': {e}")

        if not size_selected:
            print("Could not explicitly select 256 storage option; continuing without explicit size selection")

        for color in COLORS:
            print(f"Checking color: {color}")
            clicked = False
            try:
                clicked = try_click_color(page, color)
            except Exception as e:
                print(f"Error clicking {color}: {e}")

            if not clicked:
                print(f"Could not locate clickable element for '{color}'. Continuing.")
                continue

            # give page time to update after clicking
            time.sleep(2)

            # look for out-of-stock text anywhere on the page
            try:
                count = page.locator(f"text={OUT_OF_STOCK_TEXT}").count()
            except Exception:
                count = 0

            if count == 0:
                # text NOT found => likely available
                msg = f"[ahamoチェック] 在庫の可能性: {color}\n{URL}"
                print("Out-of-stock text not found -> sending webhook", msg)
                send_discord(webhook, msg)
                # If you want to stop after first positive, uncomment next line
                # break
            else:
                print(f"'{OUT_OF_STOCK_TEXT}' found for {color} -> likely sold out")

        browser.close()


if __name__ == "__main__":
    main()

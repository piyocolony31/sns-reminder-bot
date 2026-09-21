import os
import sys
import json
import logging
from datetime import datetime, date
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

# ログ設定
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

HOTEL_CODE = "0000001834"
LODGER_CODE = "0_1_2_3_4_6"
LODGER_NUM = "3_0_0_0_0_0"  # 大人3名
STAYS = "1"

# 検索対象期間 (2026年12月1日 〜 2027年3月31日)
MIN_SEARCH_DATE = date(2026, 12, 1)
MAX_SEARCH_DATE = date(2027, 3, 31)

# 日曜日のみチェックするかどうか (デフォルト: True、SUNDAY_ONLY=false で全曜日チェック)
SUNDAY_ONLY = os.getenv("SUNDAY_ONLY", "true").lower() == "true"

# LINE & Discord 通知用環境変数
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_GROUP_ID = os.getenv("LINE_GROUP_ID") or os.getenv("LINE_TO_ID")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL") or os.getenv("DISCORD_WEBHOOK_AUTOCHECK_URL") or os.getenv("DISCORD_HOUSEHOLD_WEBHOOK_URL")


def get_target_year_months():
    """
    検索対象の年月 (YYYYMM) のリストを取得。
    MIN_SEARCH_DATE から MAX_SEARCH_DATE の範囲の年月を抽出。
    """
    today = date.today()
    start_date = max(today, MIN_SEARCH_DATE)

    ym_set = set()
    current = date(start_date.year, start_date.month, 1)

    while current <= MAX_SEARCH_DATE:
        ym_set.add(current.strftime("%Y%m"))
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)

    return sorted(list(ym_set))


def fetch_monthly_calendar(ym_str: str):
    """
    d-reserve.jp から指定年月のカレンダー情報を取得する (urllib 使用)。
    """
    base_url = f"https://d-reserve.jp/v1/search/hotels/{HOTEL_CODE}/calendar"
    params = {
        "fromYM": ym_str,
        "toYM": ym_str,
        "lodgerCode": LODGER_CODE,
        "lodgerNum": LODGER_NUM,
        "stays": STAYS,
        "onlyAllLanguagesPlan": "false",
        "onlyAllRankPlan": "false",
    }
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept-Language": "ja",
    })

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("data", [])
    except Exception as e:
        logging.error(f"APIリクエストエラー ({ym_str}): {e}")
        return []


def build_reservation_url(hotel_code: str, ci_date_str: str) -> str:
    """
    予約一覧ページのURLを生成する。
    ci_date_str: YYYY-MM-DD -> YYYYMMDD
    """
    formatted_ci = ci_date_str.replace("-", "")
    return (
        f"https://d-reserve.jp/calendar?"
        f"hotelCode={hotel_code}&"
        f"ci={formatted_ci}&"
        f"lt001={LODGER_CODE}&"
        f"lnum001={LODGER_NUM}&"
        f"sortKeyOrder=0"
    )


def check_kogetsu_sunday_vacancies():
    """
    秀峰閣 湖月 の12月以降〜3月末までの日曜日空室チェックを実施する。
    ThreadPoolExecutor を使用して並列取得する。
    """
    target_yms = get_target_year_months()
    logging.info(f"検索対象年月: {target_yms}")

    found_vacancies = []

    # 並列で各月を高速取得
    month_rooms_map = {}
    with ThreadPoolExecutor(max_workers=len(target_yms) or 1) as executor:
        future_to_ym = {executor.submit(fetch_monthly_calendar, ym): ym for ym in target_yms}
        for future in as_completed(future_to_ym):
            ym = future_to_ym[future]
            try:
                rooms = future.result()
                month_rooms_map[ym] = rooms
            except Exception as e:
                logging.error(f"取得失敗 ({ym}): {e}")
                month_rooms_map[ym] = []

    # 取得結果の解析
    for ym_str in target_yms:
        rooms = month_rooms_map.get(ym_str, [])
        for room in rooms:
            room_name = room.get("name", "部屋タイプ不明")
            daily_list = room.get("dailySalesStatusList", [])

            for daily in daily_list:
                sales_date_str = daily.get("salesDate")
                if not sales_date_str:
                    continue

                sales_date = datetime.strptime(sales_date_str, "%Y-%m-%d").date()

                # 条件1: 対象期間内 (2026-12-01 〜 2027-03-31)
                if not (MIN_SEARCH_DATE <= sales_date <= MAX_SEARCH_DATE):
                    continue

                # 条件2: 日曜日のみチェックする場合 (weekday == 6)
                if SUNDAY_ONLY and sales_date.weekday() != 6:
                    continue

                # 条件3: 空室あり (salesAvailable == True)
                if daily.get("salesAvailable") is True:
                    price_info = daily.get("lowestPlanForRegular") or daily.get("lowestPlanForMember")
                    total_price = price_info.get("totalPrice") if price_info else None
                    stock_num = daily.get("stockNum")

                    res_url = build_reservation_url(HOTEL_CODE, sales_date_str)

                    vacancy_item = {
                        "date": sales_date_str,
                        "day_of_week": "日",
                        "room_name": room_name,
                        "price": total_price,
                        "stock_num": stock_num,
                        "url": res_url,
                    }
                    found_vacancies.append(vacancy_item)

    return found_vacancies


def send_http_post(url: str, headers: dict, data_bytes: bytes):
    """標準ライブラリを使用した POST リクエスト"""
    req_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"
    }
    req_headers.update(headers)
    req = urllib.request.Request(url, data=data_bytes, headers=req_headers, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status


def notify_line(message_text: str):
    """LINE Push API を使用して通知"""
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_GROUP_ID:
        logging.info("LINE_CHANNEL_ACCESS_TOKEN または LINE_GROUP_ID が設定されていないため、LINE通知をスキップします。")
        return False

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
    }
    payload = {
        "to": LINE_GROUP_ID,
        "messages": [
            {
                "type": "text",
                "text": message_text,
            }
        ],
    }

    try:
        data_bytes = json.dumps(payload).encode("utf-8")
        status = send_http_post(url, headers, data_bytes)
        logging.info(f"LINE通知を送信しました (status: {status})。")
        return True
    except Exception as e:
        logging.error(f"LINE通知送信エラー: {e}")
        return False


def notify_discord(message_text: str):
    """Discord Webhook を使用して通知"""
    if not DISCORD_WEBHOOK_URL:
        logging.info("DISCORD_WEBHOOK_URL が設定されていないため、Discord通知をスキップします。")
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


def format_notification_message(vacancies):
    """通知メッセージのフォーマット"""
    lines = [
        "🎉【秀峰閣 湖月】空室が見つかりました！",
        "12月〜3月・日曜日1泊（大人3名）のプランに空きがあります。",
        "",
    ]

    by_date = {}
    for v in vacancies:
        d = v["date"]
        if d not in by_date:
            by_date[d] = []
        by_date[d].append(v)

    for d_str, items in sorted(by_date.items()):
        lines.append(f"📅 宿泊希望日: {d_str} (日)")
        for item in items:
            price_str = f"￥{item['price']:,}" if item['price'] else "料金要確認"
            lines.append(f"  ・{item['room_name']} ({price_str})")
        lines.append(f"🔗 予約URL: {items[0]['url']}")
        lines.append("")

    return "\n".join(lines).strip()


def main():
    logging.info("=== 秀峰閣 湖月 空室チェック開始 ===")
    vacancies = check_kogetsu_sunday_vacancies()

    if not vacancies:
        logging.info("該当する日曜日1泊の空室は見つかりませんでした。")
        sys.exit(0)

    logging.info(f"空室検出数: {len(vacancies)}件")
    msg = format_notification_message(vacancies)
    logging.info(f"\n--- 送信メッセージ ---\n{msg}\n---------------------")

    sent_discord = notify_discord(msg)

    if not sent_discord:
        logging.info("DISCORD_WEBHOOK_URL が設定されていないか、送信に失敗しました。コンソール出力のみ完了しました。")


if __name__ == "__main__":
    main()

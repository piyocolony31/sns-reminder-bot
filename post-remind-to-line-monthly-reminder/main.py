import os
import requests

# LINE API トークン・グループID
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_GROUP_ID = os.environ["LINE_GROUP_ID"]

# ヘッダー情報
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
}

# メッセージデータ
data = {
    "to": LINE_GROUP_ID,
    "messages": [
        {
            "type": "template",
            "altText": "次会えるの、いつだっけ？",
            "template": {
                "type": "buttons",
                "thumbnailImageUrl": "https://example.com/honda_tsubasa.jpg",  # 画像URLは差し替えてください
                "imageAspectRatio": "rectangle",
                "imageSize": "cover",
                "imageBackgroundColor": "#FFFFFF",
                "title": "次会えるの、いつだっけ？",
                "text": "どっちか教えて？",
                "actions": [
                    {
                        "type": "message",
                        "label": "決定済み。教えてあげる",
                        "text": "ちょっと待ってな..."
                    },
                    {
                        "type": "message",
                        "label": "未定",
                        "text": "次回の予定について話す時間がほしい。¥n来月の土曜日で22時から都合の良い日を教えてくれないか。"
                    }
                ]
            }
        }
    ]
}

# メッセージ送信関数
def send_line_message():
    url = "https://api.line.me/v2/bot/message/push"
    response = requests.post(url, headers=headers, json=data)
    print(response.status_code, response.json())

# 実行
if __name__ == "__main__":
    send_line_message()
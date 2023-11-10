import os
import requests

LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_GROUP_ID = os.environ["LINE_GROUP_ID"]

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
}

data = {
    "to": LINE_GROUP_ID,
    "messages": [
        {
            "type": "template",
            "altText": "明日の定例会は参加する？",
            "template": {
                "type": "buttons",
                "thumbnailImageUrl": "https://pinfluencer.net/wp-content/uploads/2016/08/-%E9%BB%92%E7%8C%AB%E3%80%80%E3%82%B3%E3%82%B9%E3%83%97%E3%83%AC-e1471934121461.jpg",
                "imageAspectRatio": "rectangle",
                "imageSize": "cover",
                "imageBackgroundColor": "#FFFFFF",
                "title": "定例会の出欠確認",
                "text": "明日の定例会、参加する？",
                "actions": [
                    {
                        "type": "message",
                        "label": "参加",
                        "text": "参加するよ！"
                    },
                    {
                        "type": "message",
                        "label": "欠席",
                        "text": "ごめん､欠席する..."
                    },
                    {
                        "type": "message",
                        "label": "未定(いつ分かるか追記してね)",
                        "text": "未定だなぁ...いつ分かるか5秒後に送るから待ってて！"
                    }
                ]
            }
        }
    ]
}

def send_line_message():
    url = "https://api.line.me/v2/bot/message/push"
    response = requests.post(url, headers=headers, json=data)
    print(response.status_code, response.json())

if __name__ == "__main__":
    send_line_message()

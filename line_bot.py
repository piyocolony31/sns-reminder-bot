import os
import requests

LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_GROUP_ID = os.environ["LINE_GROUP_ID"]  # 追加

def send_line_message():
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    data = {
        "to": LINE_GROUP_ID,  # 変更
        "messages": [
            {
                "type": "text",
                "text": "明日の定例会は参加する？",
                "quickReply": {
                    "items": [
                        {
                            "type": "action",
                            "action": {
                                "type": "message",
                                "label": "参加",
                                "text": "参加"
                            }
                        },
                        {
                            "type": "action",
                            "action": {
                                "type": "message",
                                "label": "欠席",
                                "text": "欠席"
                            }
                        },
                        {
                            "type": "action",
                            "action": {
                                "type": "message",
                                "label": "未定",
                                "text": "未定（いつわかるかも追記してね）"
                            }
                        }
                    ]
                }
            }
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    print(response.status_code, response.json())

if __name__ == "__main__":
    send_line_message()

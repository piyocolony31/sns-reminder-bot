import sys
import requests
import json

def send_discord_with_button_notification(webhook_url, content, button_label, button_response):
    data = {
        "content": content,
        "components": [
            {
                "type": 1,
                "components": [
                    {
                        "type": 2,
                        "label": button_label,
                        "style": 1,
                        "custom_id": "button_click"
                    }
                ]
            }
        ]
    }

    response = requests.post(webhook_url, headers={"Content-Type": "application/json"}, data=json.dumps(data))
    if response.status_code == 200:
        print("Notification sent successfully.")
    else:
        print(f"Failed to send notification: {response.status_code}")
    
    # Handling button interaction (this part needs to be managed by your bot)
    # For simplicity, we'll just print the response message here
    print(f"Button response: {button_response}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python notify_discord.py <webhook_url> <content> <button_label> <button_response>")
        sys.exit(1)
    
    webhook_url = sys.argv[1]
    content = sys.argv[2]
    button_label = sys.argv[3]
    button_response = sys.argv[4]

    send_discord_with_button_notification(webhook_url, content, button_label, button_response)

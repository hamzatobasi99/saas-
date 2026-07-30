import requests

# رابط السيرفر المحلي الخاص بك
url = "http://127.0.0.1:8000/webhook"

# البيانات الوهمية التي تحاكي رسالة حقيقية قادمة من Meta
payload = {
  "object": "whatsapp_business_account",
  "entry": [
    {
      "changes": [
        {
          "value": {
            "messages": [
              {
                "from": "962779455273",  # 👈 ضع رقم هاتفك هنا
                "type": "text",
                "text": {
                  "body": "مرحبا، هل يمكنك مساعدتي؟"
                }
              }
            ]
          }
        }
      ]
    }
  ]
}

print("Initiating direct local test to bypass Meta...")
try:
    # إرسال الطلب الوهمي إلى السيرفر
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")
except Exception as e:
    print(f"Connection Error: {e}")
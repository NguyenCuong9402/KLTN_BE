import requests

from app.enums import TOKEN_BOT_TELE

#https://api.telegram.org/botTOKEN/getChat?chat_id=1497977059

# https://api.telegram.org/bot7681347480:AAFM7ytizPlasiURlOiIGQBs7eMGeUWrHAE/getUpdates

# web hook -> Khi bật ngrok sẽ có cách nhận luôn tin nhắn.
# https://api.telegram.org/botTOKEN/setWebhook?url=YOUR_WEBHOOK_URL
# https://api.telegram.org/botTOKEN/getWebhookInfo
# https://api.telegram.org/botTOKEN/deleteWebhook

# Gửi ảnh
# https://api.telegram.org/botTOKEN/sendPhoto?chat_id=CHAT_ID&photo=IMAGE_URL


# Thay bằng token bot của bạn
chat_id_cuong = "1497977059"
chat_id_loc = "1540990172"# Chat ID của bạn
MESSAGE = "Chào bạn, tôi là bot. Còn bạn là top"

url = f"https://api.telegram.org/bot{TOKEN_BOT_TELE}/sendMessage"
payload = {"chat_id": chat_id_cuong, "text": MESSAGE}

response = requests.post(url, json=payload)

import requests

from app.enums import TOKEN_BOT_TELE


# https://api.telegram.org/bot7681347480:AAFM7ytizPlasiURlOiIGQBs7eMGeUWrHAE/getUpdates
# Thay bằng token bot của bạn
chat_id_cuong = "1497977059"
chat_id_loc = "1540990172"# Chat ID của bạn
MESSAGE = "Chào bạn, tôi là bot. Còn bạn là top"

url = f"https://api.telegram.org/bot{TOKEN_BOT_TELE}/sendMessage"
payload = {"chat_id": chat_id_cuong, "text": MESSAGE}

response = requests.post(url, json=payload)

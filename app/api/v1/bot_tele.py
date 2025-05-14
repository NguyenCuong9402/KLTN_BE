
from flask import Blueprint, request

from app.utils import command_dict, sendMessage


api = Blueprint('bot_tele', __name__)

# web hook -> Khi bật ngrok sẽ có cách nhận luôn tin nhắn.
# https://api.telegram.org/botTOKEN/setWebhook?url=YOUR_WEBHOOK_URL
# https://api.telegram.org/botTOKEN/getWebhookInfo
# https://api.telegram.org/botTOKEN/deleteWebhook

# Gửi ảnh
# https://api.telegram.org/botTOKEN/sendPhoto?chat_id=CHAT_ID&photo=IMAGE_URL


@api.route('', methods=['POST'])
def web_hook_tele():
    data = request.get_json()

    if 'message' not in data:
        print("Không có message")
        return 'Invalid message', 200

    message_obj = data['message']

    if 'text' not in message_obj:
        return 'Unsupported message type', 200
    chat_id = data['message']['chat']['id']
    message = data['message']['text']

    if not chat_id:
        return 'Invalid message', 200

    parts = message.strip().split(' ', 1)  # Tách theo khoảng trắng và giới hạn 2 phần

    if parts:  # Kiểm tra nếu có đúng 2 phần
        command = parts[0]  # Phần đầu tiên (lệnh)
        content = parts[1] if len(parts) > 1 else ''
        # Kiểm tra lệnh và gọi các function tương ứng
        func = command_dict.get(command)
        if func:
            func(chat_id, content)  # Gọi hàm tương ứng với lệnh
        else:
            MESSAGE = f"Lệnh không hợp lệ"
            sendMessage(chat_id, MESSAGE)
            return 'Invalid command', 200

    else:
        MESSAGE = f"Lệnh không hợp lệ"
        sendMessage(chat_id, MESSAGE)
        return 'Invalid message format', 200

    return 'OK', 200




import os
import threading

from app.message_broker import (RabbitMQConsumerSendMailConsumer)


def start_consumers_in_single_thread(app):
    """
    Hàm này chạy tất cả các consumers trong cùng một thread.
    Đảm bảo app context tồn tại trong thread.
    """
    try:
        # Tạo các consumer
        consumers = [
            RabbitMQConsumerSendMailConsumer(),
        ]

        # Chạy các consumer trong app context
        with app.app_context():
            for consumer in consumers:
                consumer.start_consuming()

    except Exception as e:
        print(f"[Error] Error in starting consumers: {e}")


def run_consumers_in_thread(app):
    """
    Chạy tất cả các consumer trong một thread duy nhất.
    """
    thread = threading.Thread(target=start_consumers_in_single_thread, args=(app,))
    thread.daemon = True
    thread.start()
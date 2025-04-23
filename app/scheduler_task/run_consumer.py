import threading
from app.message_broker import RabbitMQConsumerSendMailConsumer, RabbitMQConsumerGenerativeAIConsumer

def start_consumer(consumer_class, app):
    """
    Hàm này sẽ được gọi trong từng thread để bắt đầu consumer.
    Đảm bảo app context tồn tại trong thread.
    """
    try:
        consumer = consumer_class()
        with app.app_context():  # Đảm bảo app context tồn tại trong thread
            consumer.start_consuming()
    except Exception as e:
        print(f"[Error] Error in consumer: {e}")

def run_consumers_in_thread(app):
        consumers = [
            RabbitMQConsumerSendMailConsumer,
            RabbitMQConsumerGenerativeAIConsumer
        ]

        for consumer_class in consumers:
            thread = threading.Thread(target=start_consumer, args=(consumer_class,app))
            thread.daemon = True  # Để thread kết thúc khi app dừng
            thread.start()
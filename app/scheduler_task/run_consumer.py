import threading

from app.message_broker import (RabbitMQConsumerSendMailConsumer, RabbitMQConsumerGenerateReportConsumer
, RabbitMQConsumerStatisticsConsumer)

def start_consumer(consumer_class, app):
    consumer = consumer_class()
    with app.app_context():  # Đảm bảo app context tồn tại trong thread
        consumer.start_consuming()

def run_consumers_in_thread(app):
        consumers = [
            RabbitMQConsumerSendMailConsumer,
            # RabbitMQConsumerGenerateReportConsumer,
            # RabbitMQConsumerStatisticsConsumer
        ]

        for consumer_class in consumers:
            thread = threading.Thread(target=start_consumer, args=(consumer_class,app))
            thread.daemon = True  # Để thread kết thúc khi app dừng
            thread.start()
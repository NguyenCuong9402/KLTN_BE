import threading

from app.message_broker import RabbitMQConsumerSendMail, RabbitMQConsumerGenerateReport, RabbitMQConsumerStatistics


def start_consumer(consumer_class):
    consumer = consumer_class()
    consumer.start_consuming()

def run_consumers_in_thread():
        consumers = [
            RabbitMQConsumerSendMail,
            RabbitMQConsumerGenerateReport,
            RabbitMQConsumerStatistics
        ]

        for consumer_class in consumers:
            thread = threading.Thread(target=start_consumer, args=(consumer_class,))
            thread.daemon = True  # Để thread kết thúc khi app dừng
            thread.start()
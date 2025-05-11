import pika
import json
import abc
from app.settings import DevConfig

CONFIG = DevConfig


class BaseRabbitMQProducer(abc.ABC):
    def __init__(self):
        self.exchange_name = CONFIG.EXCHANGE_NAME
        self.exchange_type = CONFIG.EXCHANGE_TYPE
        self.credentials = pika.PlainCredentials(CONFIG.USER_RABBIT, CONFIG.PASSWORD_RABBIT)
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=CONFIG.HOST_RABBIT, port=CONFIG.PORT_RABBIT, credentials=self.credentials)
        )
        self.channel = self.connection.channel()
        self.channel.exchange_declare(
            exchange=self.exchange_name,
            exchange_type=self.exchange_type,
            durable=True,
        )

    @property
    @abc.abstractmethod
    def routing_key(self):
        """Subclasses must define a routing key."""
        pass

    @abc.abstractmethod
    def expiration(self):
        """Subclasses must define a routing key."""
        pass

    def call(self, message):
        print(f"[{self.__class__.__name__}] Sending message: {message}")
        self.channel.basic_publish(
            exchange=self.exchange_name,
            routing_key=self.routing_key,
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2, expiration=self.expiration),  # Ensure message durability
        )


class RabbitMQProducerSendMail(BaseRabbitMQProducer):
    @property
    def routing_key(self):
        return CONFIG.SEND_MAIL_ROUTING_KEY

    @property
    def expiration(self):
        return tinh_ttl(phut=3)

    def __init__(self):
        super().__init__()
        self.channel.queue_declare(queue=CONFIG.SEND_MAIL_QUEUE, durable=True)


def tinh_ttl(phut=0, giay=0):
    """
    Tính TTL (Time-To-Live) cho thông điệp trong RabbitMQ.

    Tham số:
    - phut: Số phút.
    - giay: Số giây.

    Trả về:
    - TTL dưới dạng chuỗi mili giây.
    """
    ttl_miligiay = (phut * 60 + giay) * 1000
    return str(ttl_miligiay)
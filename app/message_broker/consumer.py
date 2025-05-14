import pika
import json

from flask import current_app

from app.enums import TYPE_ACTION_SEND_MAIL
from app.settings import DevConfig
from flask_mail import Message as MessageMail
from app.extensions import mail

CONFIG = DevConfig


class BaseRabbitMQConsumer:
    def __init__(self, queue_name, routing_key):
        self.queue_name = queue_name
        self.routing_key = routing_key
        self.credentials = pika.PlainCredentials(CONFIG.USER_RABBIT, CONFIG.PASSWORD_RABBIT)
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=CONFIG.HOST_RABBIT, port=CONFIG.PORT_RABBIT, credentials=self.credentials)
        )
        self.channel = self.connection.channel()

        self.channel.exchange_declare(exchange=CONFIG.EXCHANGE_NAME, exchange_type='direct', durable=True)

        self.channel.queue_declare(queue=self.queue_name, durable=True)
        self.channel.queue_bind(exchange=CONFIG.EXCHANGE_NAME, queue=self.queue_name, routing_key=self.routing_key)

    def callback(self, ch, method, properties, body):
        print(f"[{self.__class__.__name__}] Received message: {body.decode()}")
        self.process_message(json.loads(body))
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def start_consuming(self):
        self.channel.basic_consume(queue=self.queue_name, on_message_callback=self.callback)
        print(f"[{self.__class__.__name__}] Waiting for messages...")
        self.channel.start_consuming()

    def process_message(self, message):
        raise NotImplementedError("Subclasses must implement process_message method")


class RabbitMQConsumerSendMailConsumer(BaseRabbitMQConsumer):
    def __init__(self):
        super().__init__(CONFIG.SEND_MAIL_QUEUE, CONFIG.SEND_MAIL_ROUTING_KEY)

    def process_message(self, message):
        type_action = message.get('type_action', None)
        email = message.get('email')
        if type_action in[TYPE_ACTION_SEND_MAIL['REGISTER'], TYPE_ACTION_SEND_MAIL['OPEN_ACCOUNT'],
                          TYPE_ACTION_SEND_MAIL['UPDATE_ACCOUNT'], TYPE_ACTION_SEND_MAIL['FORGET_PASS'],
                          TYPE_ACTION_SEND_MAIL['NEW_PASSWORD'], TYPE_ACTION_SEND_MAIL['NEW_STAFF']] and email:

            email =  message.get('email')
            html = message.get('html', None)
            with current_app.app_context():  # Thêm application context
                msg = MessageMail(message.get('title', 'MÃ XÁC THỰC ĐĂNG KÝ TÀI KHOẢN C&N'), recipients=email)
                if html is not None:
                    msg.html = html
                else:
                    msg.body = message.get('body_mail')
                mail.send(msg)
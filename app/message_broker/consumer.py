import pika
import json

from flask import current_app

from app.enums import TYPE_ACTION_SEND_MAIL
from app.settings import DevConfig
import os
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

        if type_action == TYPE_ACTION_SEND_MAIL['REGISTER'] and email:
            email =  message.get('email')

            with current_app.app_context():  # Thêm application context
                msg = MessageMail('Mã xác thực:', recipients=email)
                msg.body = message.get('body_mail')
                mail.send(msg)

        elif type_action == TYPE_ACTION_SEND_MAIL['CHANGE_PASS']:
            pass
        elif type_action == TYPE_ACTION_SEND_MAIL['FORGET_PASS']:
            pass


class RabbitMQConsumerGenerateReportConsumer(BaseRabbitMQConsumer):
    def __init__(self):
        super().__init__(CONFIG.GENERATE_REPORT_QUEUE, CONFIG.GENERATE_REPORT_ROUTING_KEY)

    def process_message(self, message):
        print(f"[GenerateReport] Generating report: {message}")


class RabbitMQConsumerStatisticsConsumer(BaseRabbitMQConsumer):
    def __init__(self):
        super().__init__(CONFIG.STATISTICS_QUEUE, CONFIG.STATISTICS_ROUTING_KEY)

    def process_message(self, message):
        print(f"[Statistics] Processing statistics: {message}")

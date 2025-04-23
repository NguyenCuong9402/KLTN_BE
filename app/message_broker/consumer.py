import pika
import json
from flask import current_app
from flask_mail import Message as MessageMail

from app.enums import TYPE_ACTION_SEND_MAIL, PROMPT_AI
from app.generativeai import search_ai
from app.settings import DevConfig
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

    def start_consuming(self):
        self.channel.basic_consume(queue=self.queue_name, on_message_callback=self.callback)
        print(f"[{self.__class__.__name__}] Waiting for messages...")
        self.channel.start_consuming()

    def callback(self, ch, method, properties, body):
        try:
            print(f"[{self.__class__.__name__}] Received message: {body.decode()}")
            response = self.process_message(json.loads(body))

            # Nếu có reply_to và correlation_id → là RPC call
            if properties.reply_to and properties.correlation_id:
                ch.basic_publish(
                    exchange='',
                    routing_key=properties.reply_to,
                    properties=pika.BasicProperties(correlation_id=properties.correlation_id),
                    body=json.dumps(response)
                )

        except Exception as e:
            print(f"[{self.__class__.__name__}] Error processing message: {e}")

        ch.basic_ack(delivery_tag=method.delivery_tag)

    def process_message(self, message):
        raise NotImplementedError("Subclasses must implement process_message method")


class RabbitMQConsumerSendMailConsumer(BaseRabbitMQConsumer):
    def __init__(self):
        super().__init__(CONFIG.SEND_MAIL_QUEUE, CONFIG.SEND_MAIL_ROUTING_KEY)

    def process_message(self, message):
        type_action = message.get('type_action')
        email = message.get('email')

        if type_action in [
            TYPE_ACTION_SEND_MAIL['REGISTER'],
            TYPE_ACTION_SEND_MAIL['OPEN_ACCOUNT'],
            TYPE_ACTION_SEND_MAIL['UPDATE_ACCOUNT']
        ] and email:
            with current_app.app_context():
                msg = MessageMail(
                    subject=message.get('title', 'MÃ XÁC THỰC ĐĂNG KÝ TÀI KHOẢN C&M'),
                    recipients=email
                )
                msg.body = message.get('body_mail')
                mail.send(msg)
            print("[SendMail] Email sent.")


class RabbitMQConsumerGenerativeAIConsumer(BaseRabbitMQConsumer):
    def __init__(self):
        super().__init__(CONFIG.GENERATIVE_AI_QUEUE, CONFIG.GENERATIVE_AI_ROUTING_KEY)

    def process_message(self, message):
        text_search = message.get('text_search', '')
        name_type = message.get('name_type', [])

        result = search_ai(PROMPT_AI, text_search, name_type)

        return result  # ← gửi trả lại producer

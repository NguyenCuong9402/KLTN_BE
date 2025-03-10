
import json

from app.message_broker import RabbitMQProducerSendMail, RabbitMQProducerGenerateReport, RabbitMQProducerStatistics


def send_mail_message():
    producer = RabbitMQProducerSendMail()
    message = {
        "to": "user@example.com",
        "subject": "Test Email",
        "body": "This is a test email."
    }
    print(f"Sending message to {producer.routing_key}: {json.dumps(message)}")
    producer.call(message)

def send_generate_report_message():
    producer = RabbitMQProducerGenerateReport()
    message = {
        "report_id": 123,
        "type": "monthly",
        "details": "Generating a monthly report."
    }
    print(f"Sending message to {producer.routing_key}: {json.dumps(message)}")
    producer.call(message)

def send_statistics_message():
    producer = RabbitMQProducerStatistics()
    message = {
        "stats_id": 456,
        "metric": "engagement",
        "value": 95.2
    }
    print(f"Sending message to {producer.routing_key}: {json.dumps(message)}")
    producer.call(message)

if __name__ == "__main__":
    send_mail_message()
    send_generate_report_message()
    send_statistics_message()

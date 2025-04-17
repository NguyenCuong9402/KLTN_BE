import os
from dotenv import load_dotenv

os_env = os.environ


class Config(object):
    SECRET_KEY = '3nF3Rn0'
    APP_DIR = os.path.abspath(os.path.dirname(__file__))  # This directory
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, os.pardir))

class DevConfig(Config):
    """Development configuration."""
    load_dotenv("config/.env.dev", override=True)

    # app config
    ENV = 'dev'
    DEBUG = True
    DEBUG_TB_ENABLED = True  # Disable Debug toolbar
    TEMPLATES_AUTO_RELOAD = True
    HOST = '0.0.0.0'

    # version
    VERSION = "1.23.46"

    # JWT Config
    JWT_SECRET_KEY = '1234567a@'
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']

    # mysql config
    TIME_ZONE = 'Asia/Ho_Chi_Minh'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    BK_HOST_MYSQL =  os.environ.get('BK_HOST_MYSQL', "localhost")
    BK_PORT_MYSQL = os.environ.get('BK_PORT_MYSQL', "3306")
    BK_USERNAME_MYSQL = os.environ.get('BK_USERNAME_MYSQL', "root")
    BK_PASSWORD_MYSQL = os.environ.get('BK_PASSWORD_MYSQL', "cuong942002")
    BK_DBNAME_MYSQL = os.environ.get('BK_DBNAME_MYSQL', "dev_kltn")
    SQLALCHEMY_DATABASE_URI = f'mysql://{BK_USERNAME_MYSQL}:{BK_PASSWORD_MYSQL}@{BK_HOST_MYSQL}:{BK_PORT_MYSQL}/{BK_DBNAME_MYSQL}?charset=utf8mb4'


    # redis config
    REDIS_HOST = os.environ.get('REDIS_HOST', "localhost")
    REDIS_PORT = os.environ.get('REDIS_PORT', "6379")
    REDIS_DB = 2
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)

    # email config
    ADMIN_EMAIL = os.environ.get('MAIL_USERNAME', "cn.company.enterprise@gmail.com" )
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', "cn.company.enterprise@gmail.com" )
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', "gmve beaj gvgc juqb" )
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME', "cn.company.enterprise@gmail.com" )
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True

    # website url
    BASE_URL_WEBSITE = os.environ.get('BASE_URL_WEBSITE', "http://localhost:5012" )

    # Config Mongodb

    BK_HOST_MONGODB = os.environ.get("BK_HOST_MONGODB", "localhost")
    BK_PORT_MONGODB = os.environ.get("BK_PORT_MONGODB", "27017")
    BK_USERNAME_MONGODB = os.environ.get("BK_USERNAME_MONGODB", "root")
    BK_PASSWORD_MONGODB = os.environ.get("BK_PASSWORD_MONGODB", "admin-password")
    MONGO_DB = os.environ.get("MONGO_DB", "dev-shop")

    MONGO_CONN = f"mongodb://{BK_USERNAME_MONGODB}:{BK_PASSWORD_MONGODB}@{BK_HOST_MONGODB}:{BK_PORT_MONGODB}/{MONGO_DB}?authSource=admin"

    # rabbitmq
    ENABLE_RABBITMQ_CONSUMER = os.environ.get("ENABLE_RABBITMQ_CONSUMER", "False").lower() == "true"
    SEND_MAIL_QUEUE = os.environ.get("SEND_MAIL_QUEUE", "send_mail_queue")
    SEND_MAIL_ROUTING_KEY = os.environ.get("SEND_MAIL_ROUTING_KEY", "send.mail")

    GENERATE_REPORT_QUEUE = os.environ.get("GENERATE_REPORT_QUEUE", "generate_report_queue")
    GENERATE_REPORT_ROUTING_KEY = os.environ.get("GENERATE_REPORT_ROUTING_KEY", "generate.report")

    STATISTICS_QUEUE = os.environ.get("STATISTICS_QUEUE", "statistics_queue")
    STATISTICS_ROUTING_KEY = os.environ.get("STATISTICS_ROUTING_KEY", "statistics.process")

    EXCHANGE_NAME = os.environ.get("EXCHANGE_NAME", "default_exchange")
    EXCHANGE_TYPE = os.environ.get("EXCHANGE_TYPE", "direct")

    HOST_RABBIT = os.environ.get("HOST_RABBIT", "localhost")
    PORT_RABBIT = int(os.environ.get("PORT_RABBIT", 5672))
    USER_RABBIT = os.environ.get("USER_RABBIT", "admin")
    PASSWORD_RABBIT = os.environ.get("PASSWORD_RABBIT", "admin")

    # backup
    BACKUP = os.environ.get("BACKUP", "False").lower() == "true"




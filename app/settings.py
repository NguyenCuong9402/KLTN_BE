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
    BK_HOST_MYSQL =  os.environ.get('BK_HOST_MYSQL', "127.0.0.1")
    BK_PORT_MYSQL = os.environ.get('BK_PORT_MYSQL', "3306")
    BK_USERNAME_MYSQL = os.environ.get('BK_USERNAME_MYSQL', "root")
    BK_PASSWORD_MYSQL = os.environ.get('BK_PASSWORD_MYSQL', "cuong942002")
    BK_DBNAME_MYSQL = os.environ.get('BK_DBNAME_MYSQL', "dev_kltn")
    SQLALCHEMY_DATABASE_URI = f'mysql://{BK_USERNAME_MYSQL}:{BK_PASSWORD_MYSQL}@{BK_HOST_MYSQL}:{BK_PORT_MYSQL}/{BK_DBNAME_MYSQL}?charset=utf8mb4'

    os.environ.get('REDIS_HOST', "127.0.0.1")
    # redis config
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379
    REDIS_DB = 2
    REDIS_PASSWORD = 'cuong942002'

    # email config
    ADMIN_EMAIL = os.environ.get('MAIL_USERNAME', "cuong09042002@gmail.com" )
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', "cuong09042002@gmail.com" )
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', "cyeb cioq ynmo zirk" )
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME', "cuong09042002@gmail.com" )
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True

    # website url
    BASE_URL_WEBSITE = os.environ.get('BASE_URL_WEBSITE', "http://localhost:5012" )

    # Config Mongodb
    MONGO_CONN = "mongodb://root:bootai%402022_@192.168.1.223:27017/?authMechanism=DEFAULT"
    MONGO_DB = "dev-csoc-dev"
    BK_HOST_MONGODB = '127.0.0.1'
    BK_PORT_MONGODB = '27017'
    BK_USERNAME_MONGODB = 'root'
    BK_PASSWORD_MONGODB = ''


import os

os_env = os.environ


class Config(object):
    SECRET_KEY = '3nF3Rn0'
    APP_DIR = os.path.abspath(os.path.dirname(__file__))  # This directory
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, os.pardir))


class ProdConfig(Config):
    """Production configuration."""
    # app config
    ENV = 'prd'
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
    SQLALCHEMY_DATABASE_URI = 'mysql://root:XY58JqcxNLmy8SHN@192.168.1.223:3306/csoc-stg?charset=utf8mb4'
    TIME_ZONE = 'Asia/Ho_Chi_Minh'
    ADMIN_EMAIL = 'cuong09042002@gmail.com'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    BK_HOST_MYSQL = '192.168.1.17'
    BK_PORT_MYSQL = '3306'
    BK_USERNAME_MYSQL = 'root'
    BK_PASSWORD_MYSQL = 'cuong942002'
    BK_DBNAME_MYSQL = 'csoc-dev'

    # redis config
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379
    REDIS_DB = 2
    REDIS_PASSWORD = 'cuong942002'

    # email config
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USERNAME = 'cuong09042002@gmail.com'
    MAIL_PASSWORD = 'zhewbwhzallusent'
    MAIL_DEFAULT_SENDER = 'cuong09042002@gmail.com'
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_DEBUG = False

    # website url
    BASE_URL_WEBSITE = 'https://'

    # Config Mongodb
    MONGO_CONN = "mongodb://root:bootai%402022_@192.168.1.223:27017/?authMechanism=DEFAULT"
    MONGO_DB = "dev-csoc-dev"
    BK_HOST_MONGODB = '127.0.0.1'
    BK_PORT_MONGODB = '27017'
    BK_USERNAME_MONGODB = 'root'
    BK_PASSWORD_MONGODB = ''


class StgConfig(Config):
    """Staging configuration."""
    # app config
    ENV = 'stg'
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
    SQLALCHEMY_DATABASE_URI = 'mysql://root:XY58JqcxNLmy8SHN@192.168.1.223:3306/csoc-stg?charset=utf8mb4'
    TIME_ZONE = 'Asia/Ho_Chi_Minh'
    ADMIN_EMAIL = 'cuong09042002@gmail.com'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    BK_HOST_MYSQL = '192.168.1.17'
    BK_PORT_MYSQL = '3306'
    BK_USERNAME_MYSQL = 'root'
    BK_PASSWORD_MYSQL = 'cuong942002'
    BK_DBNAME_MYSQL = 'csoc-dev'

    # redis config
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379
    REDIS_DB = 2
    REDIS_PASSWORD = 'cuong942002'

    # email config
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USERNAME = 'cuong09042002@gmail.com'
    MAIL_PASSWORD = 'zhewbwhzallusent'
    MAIL_DEFAULT_SENDER = 'cuong09042002@gmail.com'
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_DEBUG = False

    # website url
    BASE_URL_WEBSITE = 'https://'

    # Config Mongodb
    MONGO_CONN = "mongodb://root:bootai%402022_@192.168.1.223:27017/?authMechanism=DEFAULT"
    MONGO_DB = "dev-csoc-dev"
    BK_HOST_MONGODB = '127.0.0.1'
    BK_PORT_MONGODB = '27017'
    BK_USERNAME_MONGODB = 'root'
    BK_PASSWORD_MONGODB = ''


class DevConfig(Config):
    """Development configuration."""
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
    SQLALCHEMY_DATABASE_URI = 'mysql://root:cuong942002@127.0.0.1:3306/dev_kltn?charset=utf8mb4'
    TIME_ZONE = 'Asia/Ho_Chi_Minh'
    ADMIN_EMAIL = 'cuong09042002@gmail.com'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    BK_HOST_MYSQL = '127.0.0.1'
    BK_PORT_MYSQL = '3306'
    BK_USERNAME_MYSQL = 'root'
    BK_PASSWORD_MYSQL = 'cuong942002'
    BK_DBNAME_MYSQL = 'dev_kltn'

    # redis config
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379
    REDIS_DB = 2
    REDIS_PASSWORD = 'cuong942002'

    # email config
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USERNAME = 'cuong09042002@gmail.com'
    MAIL_PASSWORD = 'cyeb cioq ynmo zirk'
    MAIL_DEFAULT_SENDER = 'cuong09042002@gmail.com'
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True

    # website url
    BASE_URL_WEBSITE = 'https://'

    # Config Mongodb
    MONGO_CONN = "mongodb://root:bootai%402022_@192.168.1.223:27017/?authMechanism=DEFAULT"
    MONGO_DB = "dev-csoc-dev"
    BK_HOST_MONGODB = '127.0.0.1'
    BK_PORT_MONGODB = '27017'
    BK_USERNAME_MONGODB = 'root'
    BK_PASSWORD_MONGODB = ''


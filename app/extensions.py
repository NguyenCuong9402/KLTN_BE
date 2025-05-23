from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_redis import Redis
from flask_migrate import Migrate
from apscheduler.schedulers.background import BackgroundScheduler
import pymongo

from .settings import DevConfig
CONFIG = DevConfig

jwt = JWTManager()

# init SQLAlchemy
db = SQLAlchemy()
migrate = Migrate()

# email
mail = Mail()

# redis
red = Redis()


# set a 5-second connection timeout
# document https://pymongo.readthedocs.io/en/stable/tutorial.html
mongo_db = pymongo.MongoClient(CONFIG.MONGO_CONN, serverSelectionTimeoutMS=5000)[CONFIG.MONGO_DB]

# os.makedirs("logs", exist_ok=True)
# app_log_handler = RotatingFileHandler('logs/app.log', maxBytes=1000000, backupCount=30, encoding="UTF-8")
#
# fh = RotatingFileHandler('logs/app_crawl.log', maxBytes=1000000, backupCount=30,
#                          encoding="UTF-8")  # create file handler that logs debug and higher level messages
#
# ch = logging.StreamHandler()  # create formatter and add it to the handlers
# formatter = logging.Formatter(
#     '%(asctime)s - %(name)s - %(levelname)s - %(message)s')  # create console handler with a higher log level
# # logger

# logger.addHandler(app_log_handler)
# # logger for crawl
#
# logger_crawl = logging.getLogger('crawl')
# logger_crawl.setLevel(logging.DEBUG)
# fh.setLevel(logging.DEBUG)
# ch.setLevel(logging.ERROR)
#
# ch.setFormatter(formatter)
# fh.setFormatter(formatter)
# # add the handlers to logger
# logger_crawl.addHandler(ch)
# logger_crawl.addHandler(fh)

# scheduler
scheduler = BackgroundScheduler(timezone="Asia/Ho_Chi_Minh")
scheduler.start()

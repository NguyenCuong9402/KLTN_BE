from datetime import timedelta

from sqlalchemy import and_
from app.enums import STATUS_ORDER
from app.extensions import db
from app.models import Orders
from app.utils import get_datetime_now
from threading import Thread

def __thread_attendance():
    with db.app.app_context():
        pass



def attendance():
    # create two new threads
    t_backup = Thread(target=__thread_attendance)
    # start the threads
    t_backup.start()
    return True

from datetime import timedelta

from sqlalchemy import and_
from app.enums import STATUS_ORDER
from app.extensions import db
from app.models import Orders
from app.utils import get_datetime_now
from threading import Thread

def __thread_resolved_orders():
    print("Running __thread_resolved_orders")
    with db.app.app_context():
        fourteen_days_ago = int((get_datetime_now() - timedelta(days=14)).timestamp())

        db.session.query(Orders).filter(
            and_(
                Orders.modified_date < fourteen_days_ago,
                Orders.status == STATUS_ORDER["DELIVERING"]
            )
        ).update({
            Orders.status: STATUS_ORDER["RESOLVED"],
        }, synchronize_session=False)

        db.session.commit()



def resolved_orders():
    # create two new threads
    t_backup = Thread(target=__thread_resolved_orders)
    # start the threads
    t_backup.start()
    return True

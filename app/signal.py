from shortuuid import uuid
from sqlalchemy import desc
from sqlalchemy.event import listens_for

from app.enums import NOTIFY_TYPE
from app.extensions import db
from app.models import Article, Comment, Reaction, Orders, Product, Notify, NotifyDetail
from app.utils import get_timestamp_now


def get_notify(user_id, notify_type, action_type=None, action_id=None):
    one_hour_ago = get_timestamp_now() - 3600 #1h

    query = Notify.query.filter(
        Notify.unread == True,
        Notify.user_id == user_id,
        Notify.modified_date > one_hour_ago,  # Lọc thông báo có modified_date lớn hơn 1 giờ trước
        Notify.notify_type == notify_type
    )

    query = query.filter(
        Notify.action_type == action_type,
        Notify.action_id == action_id
    )

    return query.order_by(desc(Notify.modified_date)).first()


def create_notify(user_id, notify_type, action_type=None, action_id=None):
    notify_data = {
        "id": str(uuid()),  # Tạo UUID cho ID
        "user_id": user_id,
        "notify_type": notify_type,
        "created_date": get_timestamp_now(),
        "modified_date": get_timestamp_now(),
        "action_type": action_type,
        "action_id": action_id,
    }

    notify = Notify(**notify_data)
    db.session.add(notify)
    db.session.commit()  # Lưu vào database

    return notify

def handle_notify(instance, user_id, notify_type, notify_detail_type,  action_type=None, action_id=None):
    notify = get_notify(user_id, notify_type, action_type, action_id, )
    if notify is None:
        notify = create_notify(user_id, notify_type, action_type, action_id)
    else:
        notify.modified_date = get_timestamp_now()

    notify_detail = NotifyDetail(id=str(uuid()), user_id=user_id, action_type=notify_detail_type,
                                 action_id=instance.id, notify_id=notify.id)
    db.session.add(notify_detail)
    db.session.commit()


def handle_article_notification(instance):
    print(f"Bài viết '{instance.id}' đã được tạo!")



def handle_comment_notification(instance):
    print(f"Bình luận mới: {instance.id}")


def handle_reaction_notification(instance):
    print(f"Phản ứng mới: {instance.id}")


def handle_orders_notification(instance):
    print(f"Đơn hàng mới: {instance.id}")

def handle_add_product_notification(instance):
    print(f"Sản phẩm mới: {instance.id}")


def handle_article_delete(instance):
    print(f"Bài viết '{instance.id}' sắp bị xóa!")

def handle_comment_delete(instance):
    print(f"Bình luận '{instance.id}' sắp bị xóa!")

def handle_reaction_delete(instance):
    print(f"Phản ứng '{instance.id}' sắp bị xóa!")

def handle_product_delete(instance):
    print(f"Sản phẩm '{instance.id}' sắp bị xóa!")

# Hàm xử lý khi model được thêm vào database
def notify_handler(mapper, connection, target):
    notification_map = {
        Article: handle_article_notification,
        Comment: handle_comment_notification,
        Reaction: handle_reaction_notification,
        Orders: handle_orders_notification,
        Product : handle_add_product_notification
    }

    handler = notification_map.get(target.__class__)
    if handler:
        handler(target)

def delete_notify_handler(mapper, connection, target):
    delete_notification_map = {
        Article: handle_article_delete,
        Reaction: handle_reaction_delete,
        Product: handle_product_delete
    }
    handler = delete_notification_map.get(target.__class__)
    if handler:
        handler(target)

# Đăng ký signal cho tất cả models
models_to_connect = [Article, Comment, Reaction, Orders, Product]
for model in models_to_connect:
    listens_for(model, "after_insert")(notify_handler)


# Đăng ký signal cho tất cả models
models_to_connect = [Article, Comment, Product]
for model in models_to_connect:
    listens_for(model, "before_delete")(delete_notify_handler)
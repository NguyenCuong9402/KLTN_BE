from shortuuid import uuid
from sqlalchemy import desc
from sqlalchemy.event import listens_for

from app.enums import NOTIFY_TYPE, CONTENT_TYPE, TYPE_REACTION
from app.extensions import db
from app.models import Article, Comment, Reaction, Orders, Product, Notify, NotifyDetail, User
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
    db.session.flush()

    return notify

def handle_notify(instance, action_detail_type, user_id, notify_type, action_type=None,  action_id=None):
    notify = get_notify(user_id, notify_type, action_type, action_id)
    if notify is None:
        notify = create_notify(user_id, notify_type, action_type, action_id)
    else:
        notify.modified_date = get_timestamp_now()

    notify_detail = NotifyDetail(id=str(uuid()), user_id=user_id, action_type=action_detail_type,
                                 action_id=instance.id, notify_id=notify.id)
    db.session.add(notify_detail)
    db.session.flush()
    db.session.commit()


def handle_article_notification(instance):
    user = User.query.filter_by(id=instance.user_id).first()

    if not user or user.group.is_staff or user.group.is_super_admin:
        return

    users = User.query.filter(User.group.has(is_staff=True)).all()
    for user in users:
        handle_notify(instance, CONTENT_TYPE["ARTICLE"], user.id, NOTIFY_TYPE["ARTICLE"])


def handle_comment_notification(instance):
    user_id = instance.ancestry.user_id if instance.ancestry_id else instance.article.user_id
    action_id = instance.ancestry_id if instance.ancestry_id else instance.article_id
    action_type = CONTENT_TYPE["COMMENT"] if instance.ancestry_id else CONTENT_TYPE["ARTICLE"]
    if instance.user_id != user_id:
        handle_notify(instance, action_detail_type=CONTENT_TYPE["COMMENT"], user_id=user_id,
                      notify_type=NOTIFY_TYPE["COMMENT"], action_type=action_type, action_id=action_id)


def handle_reaction_notification(instance):
    action_id = instance.reactable_id
    action_type = instance.category

    if action_type == TYPE_REACTION["COMMENT"]:
        comment = Comment.query.filter_by(id=action_id).first()
        user_id = comment.user_id

    else:
        article = Article.query.filter_by(id=instance.article_id).first()
        user_id = article.user_id

    if instance.user_id != user_id:
        handle_notify(instance, action_detail_type=CONTENT_TYPE["REACTION"], user_id=user_id,
                      notify_type=NOTIFY_TYPE["REACTION"], action_type=action_type, action_id=action_id)


def handle_orders_notification(instance):
    user = User.query.filter_by(id=instance.user_id).first()
    if not user or user.group.is_staff or user.group.is_super_admin:
        return
    users = User.query.filter(User.group.has(is_staff=True)).all()
    for user in users:
        handle_notify(instance, CONTENT_TYPE["ORDERS"], user.id, NOTIFY_TYPE["ORDERS"])

def handle_add_product_notification(instance):
    user = User.query.filter_by(id=instance.user_id).first()
    if not user or user.group.is_staff or user.group.is_super_admin:
        return
    users = User.query.filter(User.group.has(is_staff=True)).all()
    for user in users:
        handle_notify(instance, CONTENT_TYPE["PRODUCT"], user.id, NOTIFY_TYPE["PRODUCT"])

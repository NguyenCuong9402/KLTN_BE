from shortuuid import uuid
from sqlalchemy import desc

from app.enums import NOTIFY_TYPE, CONTENT_TYPE, TYPE_REACTION
from app.extensions import db
from app.models import Article, Comment, Notify, NotifyDetail, User
from app.utils import get_timestamp_now, sendMessage


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

    notify_detail = NotifyDetail(id=str(uuid()), user_id=instance.user_id, action_type=action_detail_type,
                                 action_id=instance.id, notify_id=notify.id)
    db.session.add(notify_detail)
    db.session.flush()
    db.session.commit()


def handle_article_notification(instance):
    user = User.query.filter_by(id=instance.user_id).first()
    if not user or user.group.is_staff or user.group.is_super_admin:
        return

    if user.chat_tele_id:
        message = f"Bạn vừa đăng bài viết mới #{instance.title}"
        sendMessage(user.chat_tele_id, message)

    users = User.query.filter(User.group.has(is_staff=True)).all()
    for admin in users:
        handle_notify(instance, CONTENT_TYPE["ARTICLE"], admin.id, NOTIFY_TYPE["ARTICLE"])
        if admin.chat_tele_id:
            message = f"Người dùng {user.email} đã đăng 1 bài viết mới"
            sendMessage(admin.chat_tele_id, message)

def handle_comment_notification(instance):
    user_id = instance.ancestry.user_id if instance.ancestry_id else instance.article.user_id
    action_id = instance.ancestry_id if instance.ancestry_id else instance.article_id
    action_type = CONTENT_TYPE["COMMENT"] if instance.ancestry_id else CONTENT_TYPE["ARTICLE"]
    if instance.user_id != user_id:
        handle_notify(instance, action_detail_type=CONTENT_TYPE["COMMENT"], user_id=user_id,
                      notify_type=NOTIFY_TYPE["COMMENT"], action_type=action_type, action_id=action_id)

    user_receive = User.query.filter_by(id=user_id).first()
    user_comment = User.query.filter_by(id=instance.user_id).first()

    action = 'trả lời bình luận' if action_type == CONTENT_TYPE["COMMENT"] else 'bình luận bài viết'

    if user_receive.chat_tele_id:
        message = f"{user_comment.full_name} đã {action} của bạn"
        sendMessage(user_receive.chat_tele_id, message)
    

def handle_reaction_notification(instance):
    action_id = instance.reactable_id
    action_type = instance.category
    
    user_reaction = User.query.filter_by(id=instance.user_id).first()
    
    if action_type == TYPE_REACTION["COMMENT"]:
        comment = Comment.query.filter_by(id=action_id).first()
        user_id = comment.user_id

    else:
        article = Article.query.filter_by(id=action_id).first()
        user_id = article.user_id
        
    user_receive = User.query.filter_by(id=user_id).first()
    
    action = 'bình luận' if action_type == TYPE_REACTION["COMMENT"] else 'bài viết'

    if user_receive.chat_tele_id:
        message = f"{user_reaction.full_name} đã reaction {action} của bạn"
        sendMessage(user_receive.chat_tele_id, message)
        

    if instance.user_id != user_id:
        handle_notify(instance, action_detail_type=CONTENT_TYPE["REACTION"], user_id=user_id,
                      notify_type=NOTIFY_TYPE["REACTION"], action_type=action_type, action_id=action_id)


def handle_orders_notification(instance):
    user = User.query.filter_by(id=instance.user_id).first()
    if not user or user.group.is_staff or user.group.is_super_admin:
        return
    #Notify User
    if user.chat_tele_id:
        message = f"Bạn vừa đặt đơn hàng mới #{instance.id}"
        sendMessage(user.chat_tele_id, message)


    #Notify Admin
    admins = User.query.filter(User.group.has(is_staff=True), User.id != instance.user_id).all()
    for admin in admins:
        handle_notify(instance, CONTENT_TYPE["ORDERS"], admin.id, NOTIFY_TYPE["ORDERS"])
        if admin.chat_tele_id:
            message = f"Người dùng {user.email} đã đặt đơn hàng mới"
            sendMessage(admin.chat_tele_id, message)
    


def handle_ship_orders_notification(instance):
    user = User.query.filter_by(id=instance.user_id).first()

    handle_notify(instance, CONTENT_TYPE["ORDERS"], user.id, NOTIFY_TYPE["DELIVERING_ORDERS"],
                            action_type=CONTENT_TYPE["ORDERS"], action_id=instance.id)

    if user.chat_tele_id:
        message = f"Đơn hàng #{instance.id} đã được vận chuyển"
        sendMessage(user.chat_tele_id, message)
from sqlalchemy.event import listens_for

from app.models import Article, Comment, Reaction, Orders, Product


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
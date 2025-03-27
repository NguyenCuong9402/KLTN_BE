import json
import os
import shortuuid
from faker import Faker
import random
import json

fake = Faker("vi_VN")

import pandas as pd
from flask import Flask
from sqlalchemy import func

from app.models import Group, User, Address
from app.extensions import db
from app.settings import DevConfig
import datetime
from pytz import timezone
import random

CONFIG = DevConfig

def get_datetime_now():
    """
    Returns the current datetime in Asia/Ho_Chi_Minh timezone.
    """
    time_zone_sg = timezone('Asia/Ho_Chi_Minh')
    return datetime.datetime.now(time_zone_sg)

def generate_vietnam_id():
    """
    Generate a fake Vietnam-style identification number (CCCD).
    """
    return f"{random.randint(0,99):02}{random.randint(100000000, 999999999)}"

def generate_vietnam_tax_code():
    """
    Generate a fake Vietnam-style tax code.
    """
    import random
    return f"{random.randint(1000000000, 9999999999)}"

class Worker:
    def __init__(self):
        app = Flask(__name__)
        app.config.from_object(CONFIG)
        db.app = app
        db.init_app(app)
        app_context = app.app_context()
        app_context.push()

    def init_group(self):
        from faker import Faker
        import random
        import datetime
        import shortuuid
        from sqlalchemy.sql.expression import func

        fake = Faker("vi_VN")

        try:
            list_group = [
                {'key': 'admin', 'name': 'Quản trị viên', 'description': 'admin', 'is_super_admin': True},
                {'key': 'user', 'name': 'Khách hàng', 'description': 'khách hàng'},
                {'key': 'director', 'name': 'Giám đốc', 'description': 'giám đốc', 'is_staff': True},
                {'key': 'accountant', 'name': 'Kế toán', 'description': 'kế toán', 'is_staff': True},
                {'key': 'hr_manager', 'name': 'Quản lý nhân sự', 'description': 'quản lý nhân sự', 'is_staff': True},
                {'key': 'employee', 'name': 'Nhân viên', 'description': 'nhân viên', 'is_staff': True}
            ]

            list_user = [
                {'email': f'{user}{role}@gmail.com', 'password': '123456789', 'full_name': f'{user.title()} {role}',
                 'group_key': role, 'phone': f"0{random.randint(3200000000, 3999999999)}", 'identification_card': generate_vietnam_id(),
                 'tax_code': generate_vietnam_tax_code(), 'join_date': datetime.datetime(2024, 1, 1),
                 'finish_date': datetime.datetime(2027, 1, 1), 'number_dependent': 0, 'gender': random.choice([0, 1]),
                 'birthday': fake.date_of_birth(minimum_age=14, maximum_age=60)
                 }
                for role in ['admin', 'user', 'director', 'employee', 'hr_manager', 'accountant']
                for user in ['cuong', 'loc']
            ]

            # Tạo thêm 100,000 user giả
            list_user.extend([
                {'email': f"{fake.user_name()}{random.randint(1000, 9999)}@gmail.com",
                 "phone": f"0{random.randint(3200000000, 3999999999)}", 'gender': random.choice([0, 1]),
                 'birthday': fake.date_of_birth(minimum_age=14, maximum_age=60),
                 "password": "123456789", "full_name": fake.name(), "group_key": "user"}
                for _ in range(10000)
            ])

            print("Thêm nhóm")
            db.session.bulk_insert_mappings(Group, [{**g, 'id': str(shortuuid.uuid())} for g in list_group])
            db.session.commit()

            group_dict = {g.key: g.id for g in Group.query.all()}

            address_ids = [a.id for a in Address.query.with_entities(Address.id).all()]

            print("Thêm người dùng")

            users_to_insert = []
            for item in list_user:
                item["group_id"] = group_dict.get(item.pop("group_key"))
                item["id"] = str(shortuuid.uuid())
                item["is_active"] = True
                item["address_id"] = random.choice(address_ids)
                users_to_insert.append(item)

            db.session.bulk_insert_mappings(User, users_to_insert)
            db.session.commit()

            print("Xonggg")

        except Exception as ex:
            print(f"Lỗi: {ex}")

    def delete_group(self):
        User.query.filter().delete()
        Group.query.filter().delete()
        db.session.commit()


if __name__ == '__main__':
    print("=" * 10, f"Starting init Address to the database on the uri: {CONFIG.SQLALCHEMY_DATABASE_URI}", "=" * 10)
    worker = Worker()
    worker.delete_group()
    worker.init_group()
    print("=" * 50, "Add address Success", "=" * 50)

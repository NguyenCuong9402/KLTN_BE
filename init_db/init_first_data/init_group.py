import json
import os
import shortuuid

import pandas as pd
from flask import Flask

from app.models import Group, User
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
        list_group = [
            {
                'key': 'admin',
                'name': 'admin',
                'description': 'admin',
                'is_super_admin': True,

            },
            {
                'key': 'user',
                'name': 'khách hàng',
                'description': 'khách hàng',
            },
            {
                'key': 'director',
                'name': 'giám đốc',
                'description': 'giám đốc',
                'is_staff': True,

            },
            {
                'key': 'accountant',
                'name': 'kế toán',
                'description': 'kế toán',
                'is_staff': True,

            },
            {
                'key': 'hr_manager',
                'name': 'quản lý nhân sự',
                'description': 'quản lý nhân sự',
                'is_staff': True,

            },
            {
                'key': 'employee',
                'name': 'nhân viên',
                'description': 'nhân viên',
                'is_staff': True,

            }
        ]

        list_user = [
            # Admin
            {
                'email': 'cuongadmin@gmail.com',
                'password': '123456789',
                'phone': '0327241194',
                'full_name': 'Nguyễn Ngọc Cương',
                'group_key': 'admin',
            },
            {
                'email': 'locadmin@gmail.com',
                'phone': '0327241194',
                'password': '123456789',
                'full_name': 'Tô Thành Lộc',
                'group_key': 'admin',
            },
            # User (Khách hàng)
            {
                'email': 'cuonguser@gmail.com',
                'phone': '0327241194',
                'password': '123456789',
                'full_name': 'Nguyễn Ngọc Cương',
                'group_key': 'user',
            },
            {
                'email': 'locuser@gmail.com',
                'phone': '0327241194',
                'password': '123456789',
                'full_name': 'Tô Thành Lộc',
                'group_key': 'user',
            },
        ]

        # Các tài khoản nhân sự, kế toán, giám đốc, nhân viên
        roles = ['director', 'employee', 'hr_manager', 'accountant']
        users = ['cuong', 'loc']

        for role in roles:
            for user in users:
                join_date = datetime.datetime(2024, 1, 1)
                finish_date = join_date + datetime.timedelta(days=3 * 365)  # +3 năm

                list_user.append({
                    'email': f'{user}{role}@gmail.com',
                    'password': '123456789',
                    'full_name': f'Cương {role}' if user == 'cuong' else f'Lộc {role}',
                    'group_key': role,
                    'phone': '0327241194',
                    'identification_card': generate_vietnam_id(),
                    'tax_code': generate_vietnam_tax_code(),
                    'join_date': join_date,
                    'finish_date': finish_date,
                    'number_dependent': 0,
                })

        list_add_group= []
        for item in list_group:
            group = Group(
                id=str(shortuuid.uuid()), **item
            )
            list_add_group.append(group)
        db.session.bulk_save_objects(list_add_group)

        for item in list_user:
            group_key = item.pop('group_key')
            group = Group.query.filter_by(key=group_key).first()
            user = User(id=str(shortuuid.uuid()), **item, group_id=group.id, is_active=True)
            db.session.add(user)
            db.session.flush()

        db.session.commit()

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

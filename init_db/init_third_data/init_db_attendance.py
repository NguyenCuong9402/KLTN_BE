import json
import os
import random

from shortuuid import uuid
import pandas as pd
from flask import Flask
from datetime import datetime, date, timedelta, time

from app.api.helper import send_result
from app.models import Group, Community, Attendance, User
from app.extensions import db
from app.settings import DevConfig

CONFIG = DevConfig


class Worker:
    def __init__(self):
        app = Flask(__name__)
        app.config.from_object(CONFIG)
        db.app = app
        db.init_app(app)
        app_context = app.app_context()
        app_context.push()

    def random_time(self, start: time, end: time) -> time:
        start_seconds = start.hour * 3600 + start.minute * 60 + start.second
        end_seconds = end.hour * 3600 + end.minute * 60 + end.second
        random_seconds = random.randint(start_seconds, end_seconds)
        hour = random_seconds // 3600
        minute = (random_seconds % 3600) // 60
        second = random_seconds % 60

        return time(hour, minute, second)

    def random_time_checkout(self, start: time, end: time) -> time:
        start_seconds = start.hour * 3600 + start.minute * 60 + start.second
        end_seconds = end.hour * 3600 + end.minute * 60 + end.second
        random_seconds = random.randint(start_seconds, end_seconds)
        hour = random_seconds // 3600
        minute = (random_seconds % 3600) // 60
        second = random_seconds % 60

        # Xác suất 2/3 có check_out, 1/3 không có (None)
        check_out = random.choice([time(hour, minute, second),
                                   time(hour, minute, second),
                                   None])

        return check_out
    
    def init_attendance(self):

        users = User.query.filter(User.group.has(is_staff=True)).all()

        for user in users:

            start_date = user.join_date
            end_date = date(2025, 3, 31)
            delta = timedelta(days=1)

            attendances = []
            while start_date <= end_date:
                # Bỏ qua Thứ Bảy và Chủ Nhật (nếu chỉ muốn ngày làm việc)
                if start_date.weekday() < 6:  # 0 = Thứ Hai, 4 = Thứ Sáu , 5:Thứ 7, 6 là chủ nhật
                    attendance = Attendance(
                        id=str(uuid()),  # Tạo UUID ngẫu nhiên
                        user_id=user.id,
                        work_date=start_date,
                        check_in=self.random_time(time(7, 0), time(8, 30)),
                        check_out=self.random_time_checkout(time(16, 30), time(19, 0))
                    )
                    attendances.append(attendance)

                start_date += delta  # Tăng ngày lên 1

            # Lưu vào database
            db.session.bulk_save_objects(attendances)
            db.session.commit()
            print(f"Đã tạo {len(attendances)} bản ghi điểm danh cho {user.email}")

    def delete_attendance(self):
        Attendance.query.filter().delete()
        db.session.commit()


if __name__ == '__main__':
    print("=" * 10, f"Starting init attendance to the database on the uri: {CONFIG.SQLALCHEMY_DATABASE_URI}", "=" * 10)
    worker = Worker()
    worker.delete_attendance()
    worker.init_attendance()
    print("=" * 50, "Add address Success", "=" * 50)

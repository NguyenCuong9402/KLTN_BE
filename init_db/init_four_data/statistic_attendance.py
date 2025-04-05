import json
import os
import random

from dateutil.relativedelta import relativedelta
from shortuuid import uuid
import pandas as pd
from flask import Flask
from datetime import datetime, date, timedelta, time
from sqlalchemy import extract
from sqlalchemy import asc

from app.api.helper import send_result
from app.enums import MONGO_COLLECTION_STATISTIC_ATTENDANCE_USER, ATTENDANCE, WORK_UNIT_TYPE
from app.models import Group, Community, Attendance, User
from app.extensions import db, mongo_db
from app.settings import DevConfig
from app.utils import save_attendance_data

CONFIG = DevConfig


class Worker:
    def __init__(self):
        app = Flask(__name__)
        app.config.from_object(CONFIG)
        db.app = app
        db.init_app(app)
        app_context = app.app_context()
        app_context.push()

    def init_attendance_mongo_db(self):

        today = date.today()
        # Tháng trước của hiện tại
        end_month = today.replace(day=1) - relativedelta(months=1)
        users = User.query.filter(User.group.has(is_staff=True)).all()
        base_date = datetime.today().date()
        check_in_attendance = datetime.combine(base_date, ATTENDANCE['CHECK_IN'])
        check_out_attendance = datetime.combine(base_date, ATTENDANCE['CHECK_OUT'])
        for user in users:
            if not user.join_date:
                continue

            # Bắt đầu từ tháng sau khi join
            start_month = user.join_date.replace(day=1) + relativedelta(months=1)

            current_month = start_month
            while current_month <= end_month:
                year = current_month.year
                month = current_month.month

                attendances = Attendance.query.filter(
                    Attendance.user_id == user.id,
                    extract("month", Attendance.work_date) == month,
                    extract("year", Attendance.work_date) == year
                ).order_by(Attendance.work_date.asc()).all()
                time_str = current_month.strftime("%m-%Y")

                data = {
                    'time_str': time_str,
                    'work_later_and_leave_early': 0,
                    'forget_checkout': 0,
                    'work_unit': 0,
                    'number_work_date': len(attendances)
                }
                for attendance in attendances:
                    if attendance.work_unit in list(WORK_UNIT_TYPE.values()):
                        data['work_unit'] += 1
                    if attendance.check_in:
                        check_in_dt = datetime.combine(base_date, attendance.check_in)
                        if check_in_dt > check_in_attendance:
                            data['work_later_and_leave_early'] += 1

                        if not attendance.check_out:
                            data['forget_checkout'] += 1
                        else:
                            check_out_dt = datetime.combine(base_date, attendance.check_out)
                            if check_out_dt < check_out_attendance:
                                data['work_later_and_leave_early'] += 1

                if data['number_work_date'] > 0:
                    vi_pham = round(
                        (data['work_later_and_leave_early'] + data['forget_checkout']) / (
                                    data['number_work_date'] * 2) * 100,
                        2
                    )
                else:
                    vi_pham = 0

                tuan_thu = 100 - vi_pham
                data['chart'] = {'Vi phạm': vi_pham,'Tuân thủ': tuan_thu,}

                # Thêm dữ liệu data vào colection mongo_db[f"attendance_statistics_{user_id}"]
                save_attendance_data(user.id, data.copy())


                # Tăng tháng lên
                current_month += relativedelta(months=1)

    def init_delete_attendance_mongo_db(self):
        collection_names = mongo_db.list_collection_names()
        for name in collection_names:
            if name.startswith(f"{MONGO_COLLECTION_STATISTIC_ATTENDANCE_USER}_"):
                mongo_db.drop_collection(name)
                print(f"Đã xóa collection: {name}")


if __name__ == '__main__':
    print("=" * 10, f"Starting init attendance to the database on the uri: {CONFIG.SQLALCHEMY_DATABASE_URI}", "=" * 10)
    worker = Worker()
    worker.init_delete_attendance_mongo_db()
    worker.init_attendance_mongo_db()
    print("=" * 50, "Add attendance Success", "=" * 50)

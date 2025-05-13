from datetime import date, datetime

from dateutil.relativedelta import relativedelta
from sqlalchemy import extract
from app.enums import ATTENDANCE, WORK_UNIT_TYPE
from app.extensions import db
from app.models import User, Attendance
from app.utils import save_attendance_data, find_attendance_data
from threading import Thread

def __thread_attendance():
    with db.app.app_context():
        today = date.today()
        # Tháng trước của hiện tại
        before_month = today.replace(day=1) - relativedelta(months=1)
        year = before_month.year
        month = before_month.month
        time_str = before_month.strftime("%Y-%m")

        users = User.query.filter(User.group.has(is_staff=True)).all()
        base_date = datetime.today().date()
        check_in_attendance = datetime.combine(base_date, ATTENDANCE['CHECK_IN'])
        check_out_attendance = datetime.combine(base_date, ATTENDANCE['CHECK_OUT'])
        for user in users:
            if not user.join_date:
                continue

            existing_data = find_attendance_data(user.id, time_str)
            if existing_data:
                continue
            attendances = Attendance.query.filter(
                Attendance.user_id == user.id,
                extract("month", Attendance.work_date) == month,
                extract("year", Attendance.work_date) == year
            ).order_by(Attendance.work_date.asc()).all()

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
                            data['number_work_date'] * 2) * 100, 2)
            else:
                vi_pham = 0
            tuan_thu = 100 - vi_pham
            data['chart'] = {'Vi phạm': vi_pham, 'Tuân thủ': tuan_thu, }
            # Thêm dữ liệu data vào colection mongo_db[f"attendance_statistics_{user_id}"]
            save_attendance_data(user.id, data.copy())



def attendance():
    # create two new threads
    t_backup = Thread(target=__thread_attendance)
    # start the threads
    t_backup.start()
    return True

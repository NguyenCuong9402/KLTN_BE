import io
from flask import send_file

import xlsxwriter
from shortuuid import uuid
from datetime import datetime, date

from flask import Blueprint, request
from marshmallow import ValidationError
from sqlalchemy import desc, asc
from sqlalchemy_pagination import paginate
from sqlalchemy import or_
from sqlalchemy import extract

from app.enums import ADMIN_KEY_GROUP, ATTENDANCE
from app.extensions import db
from flask_jwt_extended import get_jwt_identity
from app.api.helper import send_result, send_error
from app.gateway import authorization_require
from app.models import User, Group, Attendance
from app.utils import escape_wildcard, find_attendance_data
from app.validator import UserSchema, AttendanceSchema, QueryTimeSheetSchema

api = Blueprint('manage/attendance', __name__)


# Nhan vien
@api.route('/check_in', methods=['POST'])
@authorization_require()
def check_in():
    try:
        user_id = get_jwt_identity()

        user = User.query.filter_by(id=user_id).first()

        if user is None:
            return send_error(message='Tài khoản không tồn tại ')

        today = date.today()
        now = datetime.now().time()

        attendance = Attendance.query.filter_by(user_id=user_id, work_date=today).first()

        # Nếu đã check-in trước đó
        if attendance and attendance.check_in:
            return send_result(message=f'Bạn đã check in {attendance.check_in} rồi')

        # Nếu chưa có bản ghi, tạo mới
        if not attendance:
            attendance = Attendance(id=str(uuid()), user_id=user_id, work_date=today)

        # Ghi nhận giờ check-in
        attendance.check_in = now
        db.session.add(attendance)
        db.session.commit()

        data = AttendanceSchema().dump(attendance)

        return send_result(data=data, message=f'Check in thành công lúc {attendance.check_in}')

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))


@api.route('/check_out', methods=['POST'])
@authorization_require()
def check_out():
    try:
        user_id = get_jwt_identity()

        user = User.query.filter_by(id=user_id).first()

        if user is None:
            return send_error(message='Tài khoản không tồn tại ')

        today = date.today()
        now = datetime.now().time()

        attendance = Attendance.query.filter_by(user_id=user_id, work_date=today).first()

        # Nếu chưa có bản ghi, tạo mới
        if not attendance:
            return send_error(message='Bạn chưa check in')

        # Kiểm tra thời gian check-in hợp lệ
        if now < ATTENDANCE['CHECK_OUT']:
            return send_error(message='Chưa đến giờ check out')

        # Ghi nhận giờ check-in
        attendance.check_out = now
        db.session.flush()
        db.session.commit()
        data = AttendanceSchema().dump(attendance)

        return send_result(data=data, message=f'Check out thành công lúc {attendance.check_out}')

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex), code=442)


@api.route('/timekeeping', methods=['GET'])
@authorization_require()
def timekeeping():
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()

        if user is None:
            return send_error(message="Tài khoản không tồn tại")

        # Lấy tham số thời gian (mm-yyyy)
        time_str = request.args.get("time_str", type=str)
        if not time_str:
            time_obj = datetime.now()
        else:
            try:
                time_obj = datetime.strptime(time_str, "%Y-%m")
            except ValueError:
                return send_error(message="Định dạng time không hợp lệ, yêu cầu MM-YYYY")

        # Lấy tháng và năm từ time_obj
        month = time_obj.month
        year = time_obj.year

        # Truy vấn danh sách Attendance
        attendances = Attendance.query.filter(
            Attendance.user_id == user_id,
            extract("month", Attendance.work_date) == month,
            extract("year", Attendance.work_date) == year
        ).order_by(Attendance.work_date.asc()).all()

        # Serialize dữ liệu
        result = AttendanceSchema(many=True).dump(attendances)

        return send_result(data=result, message="Thành công")

    except Exception as ex:
        return send_error(message=str(ex))


@api.route('/time_check', methods=['GET'])
@authorization_require()
def time_check():
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()

        if user is None:
            return send_error(message="Tài khoản không tồn tại")

        # Truy vấn danh sách Attendance
        attendances = Attendance.query.filter(
            Attendance.user_id == user_id,
            Attendance.work_date == date.today()
        ).first()

        # Serialize dữ liệu
        result = AttendanceSchema().dump(attendances)

        data = {
            "result": result,
            "join_date": str(user.join_date)
        }
        return send_result(data=data, message="Thành công")

    except Exception as ex:
        return send_error(message=str(ex))


# Bảng chấm công

@api.route("/timesheet", methods=["GET"])
@authorization_require()
def timesheet():
    try:
        try:
            params = request.args.to_dict(flat=True)
            params = QueryTimeSheetSchema().load(params) if params else dict()
        except ValidationError as err:
            return send_error(message='INVALID_PARAMETERS_ERROR', data=err.messages)

        page = params.get('page', 1)
        page_size = params.get('page_size', 10)
        order_by = params.get('order_by', 'created_date')
        sort = params.get('sort', 'desc')
        text_search = params.get('text_search', None)
        time_str = params.get('time_str', None)

        current_date = datetime.now()

        if not time_str:
            time_obj = current_date
        else:
            try:
                time_obj = datetime.strptime(time_str, "%Y-%m")
            except ValueError:
                return send_error(message="Định dạng time không hợp lệ, yêu cầu MM-YYYY")

        # Lấy tháng và năm từ time_obj
        month = time_obj.month
        year = time_obj.year
        is_past = time_obj < current_date
        time_str = time_obj.strftime("%Y-%m")

        query = User.query.join(Group).filter(
            Group.is_staff == True,
            Group.key.notin_(ADMIN_KEY_GROUP)
        )

        if text_search:
            text_search = text_search.strip()
            text_search = text_search.lower()
            text_search = escape_wildcard(text_search)
            text_search = "%{}%".format(text_search)

            query = query.filter(
                or_(
                    User.full_name.ilike(f"%{text_search}%"),
                    User.email.ilike(f"%{text_search}%")
                )
            )

        column_sorted = getattr(User, order_by)

        query = query.order_by(desc(column_sorted)) if sort == "desc" else query.order_by(asc(column_sorted))

        paginator = paginate(query, page, page_size)

        staffs = UserSchema(many=True, only=("id", "email", "full_name")).dump(paginator.items)
        base_date = datetime.today().date()
        check_in_attendance = datetime.combine(base_date, ATTENDANCE['CHECK_IN'])
        check_out_attendance = datetime.combine(base_date, ATTENDANCE['CHECK_OUT'])
        for staff in staffs:
            data = {
                'time_str': time_str,
                'work_later_and_leave_early': 0,
                'forget_checkout': 0,
                'work_unit': 0,
                'number_work_date': 0
            }
            if is_past:
                existing_data = find_attendance_data(staff['id'], time_str)
                if existing_data:
                    data = existing_data
                # else:
                #     attendances = Attendance.query.filter(
                #         Attendance.user_id == staff['id'],
                #         extract("month", Attendance.work_date) == month,
                #         extract("year", Attendance.work_date) == year
                #     ).order_by(Attendance.work_date.asc()).all()
                #     data['number_work_date'] = len(attendances)
                #     for attendance in attendances:
                #         if attendance.work_unit in list(WORK_UNIT_TYPE.values()):
                #             data['work_unit'] += 1
                #         if attendance.check_in:
                #             check_in_dt = datetime.combine(base_date, attendance.check_in)
                #             if check_in_dt > check_in_attendance:
                #                 data['work_later_and_leave_early'] += 1
                #             if not attendance.check_out:
                #                 data['forget_checkout'] += 1
                #             else:
                #                 check_out_dt = datetime.combine(base_date, attendance.check_out)
                #                 if check_out_dt < check_out_attendance:
                #                     data['work_later_and_leave_early'] += 1

            staff['time_keeping'] = data


        response_data = dict(
            items=staffs,
            total_pages=paginator.pages if paginator.pages > 0 else 1,
            total=paginator.total,
            has_previous=paginator.has_previous,
            has_next=paginator.has_next
        )
        return send_result(data=response_data)
    except Exception as ex:
        return send_error(message=str(ex))


@api.route("/timesheet/export", methods=["GET"])
@authorization_require()
def export():
    try:
        try:
            params = request.args.to_dict(flat=True)
            params = QueryTimeSheetSchema().load(params) if params else dict()
        except ValidationError as err:
            return send_error(message='INVALID_PARAMETERS_ERROR', data=err.messages)

        order_by = params.get('order_by', 'created_date')
        sort = params.get('sort', 'desc')
        text_search = params.get('text_search', None)
        time_str = params.get('time_str', None)

        current_date = datetime.now()

        if not time_str:
            time_obj = current_date
        else:
            try:
                time_obj = datetime.strptime(time_str, "%Y-%m")
            except ValueError:
                return send_error(message="Định dạng time không hợp lệ, yêu cầu MM-YYYY")

        # Lấy tháng và năm từ time_obj
        month = time_obj.month
        year = time_obj.year
        is_past = time_obj < current_date
        time_str = time_obj.strftime("%Y-%m")

        query = User.query.join(Group).filter(
            Group.is_staff == True,
            Group.key.notin_(ADMIN_KEY_GROUP)
        )

        if text_search:
            text_search = text_search.strip()
            text_search = text_search.lower()
            text_search = escape_wildcard(text_search)
            text_search = "%{}%".format(text_search)

            query = query.filter(
                or_(
                    User.full_name.ilike(f"%{text_search}%"),
                    User.email.ilike(f"%{text_search}%")
                )
            )

        column_sorted = getattr(User, order_by)

        query = query.order_by(desc(column_sorted)).all() if sort == "desc" else query.order_by(asc(column_sorted))

        staffs = UserSchema(many=True, only=("id", "email", "full_name")).dump(query)

        base_date = datetime.today().date()
        check_in_attendance = datetime.combine(base_date, ATTENDANCE['CHECK_IN'])
        check_out_attendance = datetime.combine(base_date, ATTENDANCE['CHECK_OUT'])
        for staff in staffs:
            data = {
                'time_str': time_str,
                'work_later_and_leave_early': 0,
                'forget_checkout': 0,
                'work_unit': 0,
                'number_work_date': 0
            }
            if is_past:
                existing_data = find_attendance_data(staff['id'], time_str)
                if existing_data:
                    data = existing_data

            staff['time_keeping'] = data
        ### Viết csv
        day = date.today()
        filename = f'Bảng chấm công_{time_str}.xlsx'
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        # Tạo Worksheet mới
        worksheet = workbook.add_worksheet()

        # format
        format_cell_bold = workbook.add_format({'font_name': 'Times New Roman', 'bold': True, 'font_size': 11,
                                                'align': 'center', 'valign': 'vcenter',
                                                'bg_color': '#92d050', 'border': 1})
        center_format = workbook.add_format({'align': 'center', 'font_name': 'Times New Roman', 'border': 1,
                                             'valign': 'vcenter'})

        # merge cell : TRACEABILITY REPORT DETAIL - NAME PROJECT
        worksheet.merge_range(0, 0, 0, 5, f'Bảng chấm công - {time_str}',
                              workbook.add_format({'font_name': 'Times New Roman', 'bold': True, 'font_size': 14,
                                                   'align': 'center', 'valign': 'vcenter', 'border': 1}))
        list_name = ['EMAIL', 'TÊN NHÂN SỰ', 'SỐ CÔNG', 'SỐ NGÀY ĐIỂM DANH', 'QUÊN CHECKOUT', 'LỖI ĐIỂM DANH']

        list_map = ['email', 'full_name', 'work_unit', 'number_work_date', 'forget_checkout', 'work_later_and_leave_early']

        for index, name in enumerate(list_name):
            if index in [0, 1, 3]:
                worksheet.set_column(0, index, 40)
            else:
                worksheet.set_column(0, index, 30)

            worksheet.write(1, index, name, format_cell_bold)

        for row, staff in enumerate(staffs):
            for column, key in enumerate(list_map):
                if key in [ 'email', 'full_name']:
                    worksheet.write(row + 2, column, staff[key], center_format)
                else:
                    worksheet.write(row + 2, column, staff['time_keeping'][key], center_format)
        workbook.close()
        # Lấy nội dung của Workbook và gửi đi như là file đính kèm
        excel_data = output.getvalue()
        return send_file(io.BytesIO(excel_data), attachment_filename=filename, as_attachment=True)
    except Exception as ex:
        return send_error(message=str(ex))

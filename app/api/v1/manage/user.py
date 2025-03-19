import json
from shortuuid import uuid
from datetime import datetime, date, time

from flask import Blueprint, request
from marshmallow import ValidationError
from sqlalchemy import desc, asc
from sqlalchemy_pagination import paginate
from sqlalchemy import or_
from sqlalchemy import extract

from app.enums import ADMIN_KEY_GROUP, KEY_GROUP_NOT_STAFF, ATTENDANCE
from app.extensions import db, logger
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api.helper import send_result, send_error, convert_to_datetime
from app.models import User, Group, Files, Address, Attendance
from app.utils import trim_dict, escape_wildcard, get_timestamp_now, generate_password
from app.validator import StaffValidation, QueryParamsAllSchema, UserSchema, AttendanceSchema

api = Blueprint('manage/user', __name__)


@api.route('', methods=['POST'])
@jwt_required
def new():
    try:

        json_req = request.get_json()
        json_body = trim_dict(json_req)
        validator_input = StaffValidation()
        is_not_validate = validator_input.validate(json_body)
        if is_not_validate:
            return send_error(data=is_not_validate, message='Validate Error')


        email = json_body.get('email')
        phone = json_body.get('phone')
        group_id = json_body.get('group_id')
        avatar_id = json_body.get('avatar_id', None)

        address = json_body.pop('address')
        if json_body.get('birthday', None):
            json_body['birthday'] = convert_to_datetime(json_body.get('birthday'))

        for key, value in address.items():
            if value is None or value.strip() == '':
                return send_error(message='Vui lòng chọn địa chỉ')

        address = Address.query.filter_by(province=address.get('province'), district=address.get('district'),
                                          ward=address.get('ward')).first()
        if address is None:
            return send_error(message="Địa chỉ không hợp lệ.")

        json_body['address_id'] = address.id


        check_email = User.query.filter_by(email=email).first()
        if check_email:
            return send_error(message='Email đã được đăng ký')

        check_phone = User.query.filter_by(phone=phone).first()
        if check_phone:
            return send_error(message='SĐT đã được đăng ký')

        check_group = Group.query.filter_by(id=group_id).first()
        if check_group is None:
            return send_error(message='Chức vụ không tồn tại')

        if check_group.key in KEY_GROUP_NOT_STAFF:
            return send_error(message='Chức vụ không phù hợp')

        if avatar_id:
            check_file = Files.query.filter_by(id=avatar_id).first()
            if check_file is None:
                return send_error(message='Vui lòng tải lại ảnh')

        json_body['password'] = generate_password()

        json_body['status'] = 0 # Khi nào User đăng nhập sẽ được kích hoạt
        user = User(id=str(uuid()),**json_body)

        db.session.add(user)
        db.session.flush()
        db.session.commit()

        #send mail

        return send_result(message='Thành công')

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex), code=442)


@api.route('/check_in', methods=['POST'])
@jwt_required
def check_in():
    try:
        user_id = get_jwt_identity()

        user = User.query.filter_by(id=user_id).first()

        if user is None:
            return send_error(message='Tài khoản không tồn tại ')

        if user.group.key in KEY_GROUP_NOT_STAFF:
            return send_error(message='Tài khoản không có quyền')

        today = date.today()
        now = datetime.now().time()

        attendance = Attendance.query.filter_by(user_id=user_id, work_date=today).first()

        # Nếu đã check-in trước đó
        if attendance and attendance.check_in:
            return send_result(message='Bạn đã check in rồi')

        # Nếu chưa có bản ghi, tạo mới
        if not attendance:
            attendance = Attendance(user_id=user_id, work_date=today)

        # Kiểm tra thời gian check-in hợp lệ
        if now > ATTENDANCE['LATE_CHECK_IN']:
            return send_error(message='Bạn đã quá giờ check in')

        # Ghi nhận giờ check-in
        attendance.check_in = now
        db.session.add(attendance)
        db.session.commit()

        return send_result(message='Thành công')

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))


@api.route('/check_out', methods=['POST'])
@jwt_required
def check_out():
    try:
        user_id = get_jwt_identity()

        user = User.query.filter_by(id=user_id).first()

        if user is None:
            return send_error(message='Tài khoản không tồn tại ')

        if user.group.key in KEY_GROUP_NOT_STAFF:
            return send_error(message='Tài khoản không có quyền')

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

        return send_result(message='Thành công')

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex), code=442)

@api.route('/timekeeping', methods=['GET'])
@jwt_required
def timekeeping():
    try:
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()

        if user is None:
            return send_error(message="Tài khoản không tồn tại")

        if user.group.key in KEY_GROUP_NOT_STAFF:
            return send_error(message="Tài khoản không có quyền")

        # Lấy tham số thời gian (mm-yyyy)
        time_str = request.args.get("time", type=str)
        if not time_str:
            time_obj = datetime.now()
        else:
            try:
                time_obj = datetime.strptime(time_str, "%m-%Y")
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

@api.route("/active/<user_id>", methods=["PUT"])
@jwt_required
def active_user(user_id):
    try:
        user = User.query.filter(User.id == user_id).first()
        if not user:
            return send_error(message="Người dùng không tồn tại!")

        # Đảo trạng thái active
        user.active = not user.active
        db.session.flush()
        db.session.refresh(user)  # Cập nhật trạng thái mới sau flush()
        db.session.commit()

        # Xác định trạng thái mở/khoá
        status = "mở" if user.active else "khóa"
        return send_result(message=f"Tài khoản {user.email} đã được {status}.")

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))

@api.route("", methods=["GET"])
def get_staff():
    try:
        try:
            params = request.args.to_dict(flat=True)
            params = QueryParamsAllSchema().load(params) if params else dict()
        except ValidationError as err:
            logger.error(json.dumps({
                "message": err.messages,
                "data": err.valid_data
            }))
            return send_error(message='INVALID_PARAMETERS_ERROR', data=err.messages)


        page = params.get('page', 1)
        page_size = params.get('page_size', 10)
        order_by = params.get('order_by', 'created_date')
        sort = params.get('sort', 'desc')
        text_search = params.get('text_search', None)

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

        if order_by == "group_name":
            column_sorted = Group.name  # Thay vì User.group.name
        else:
            column_sorted = getattr(User, order_by)

        query = query.order_by(desc(column_sorted)) if sort == "desc" else query.order_by(asc(column_sorted))

        paginator = paginate(query, page, page_size)

        staffs = UserSchema(many=True).dump(paginator.items)

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


@api.route("", methods=["DELETE"])
@jwt_required
def remove_item():
    try:
        body_request = request.get_json()
        list_id = body_request.get('list_id', [])
        if len(list_id) == 0:
            return send_error(message='Chưa chọn item nào.')
        User.query.filter(User.id.in_(list_id)).delete()
        db.session.flush()
        db.session.commit()
        return send_result(message="Xóa sản phẩm thành công")
    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))



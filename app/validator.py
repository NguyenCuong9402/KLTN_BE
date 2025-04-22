import json
import typing
from datetime import date

from marshmallow import Schema, fields, validate, ValidationError, types, pre_load, validates_schema
from sqlalchemy import desc, asc

from app.enums import TYPE_REACTION, TYPE_PAYMENT_ONLINE, TYPE_PAYMENT
from app.extensions import db
from app.models import Reaction, Comment
from app.utils import REGEX_EMAIL, REGEX_VALID_PASSWORD, REGEX_FULLNAME_VIETNAMESE, REGEX_PHONE_NUMBER

# Validator
class BaseValidation(Schema):

    def custom_validate(
            self,
            data: typing.Mapping,
            *,
            many: typing.Optional[bool] = None,
            partial: typing.Optional[typing.Union[bool, types.StrSequenceOrSet]] = None
    ) -> (bool, str):
        try:
            self._do_load(data, many=many, partial=partial, postprocess=False)
        except ValidationError as exc:
            check = typing.cast(typing.Dict[str, typing.List[str]], exc.messages)
            if hasattr(self, 'define_message'):
                for key in check:
                    if key in self.define_message:
                        return False, self.define_message[key]
                return False, 'INVALID_PARAMETERS_ERROR'
            else:
                # return check
                return False, 'INVALID_PARAMETERS_ERROR'

        return True, ''


def default_schema_get_search(sort_type):
    class GetSearchValidation(BaseValidation):
        page = fields.Integer(required=False)
        page_size = fields.Integer(required=False)
        search_name = fields.String(required=False, validate=validate.Length(min=0, max=200))

        sort = fields.String(required=False,
                             validate=validate.OneOf(sort_type))
        order_by = fields.String(required=False, validate=validate.OneOf(["asc", "desc"]))

    return GetSearchValidation


class ChangePasswordValidation(BaseValidation):
    current_password = fields.String(
        required=True,
        validate=[
            validate.Length(min=1, max=16, error="Mật khẩu hiện tại phải từ 1 đến 16 ký tự."),
            validate.Regexp(REGEX_VALID_PASSWORD, error="Mật khẩu hiện tại không hợp lệ.")
        ],
        error_messages={"required": "Mật khẩu hiện tại không được để trống."}
    )

    new_password = fields.String(
        required=True,
        validate=[
            validate.Length(min=1, max=16, error="Mật khẩu mới phải từ 1 đến 16 ký tự."),
            validate.Regexp(REGEX_VALID_PASSWORD, error="Mật khẩu mới không hợp lệ.")
        ],
        error_messages={"required": "Mật khẩu mới không được để trống."}
    )

class AddressSchema(Schema):
    id = fields.String()
    province = fields.String()
    district = fields.String()
    ward = fields.String()


class GroupSchema(Schema):
    id = fields.String()
    name = fields.String()
    key = fields.String()
    is_staff = fields.Boolean()
    is_super_admin = fields.Boolean()


class FileSchema(Schema):
    id = fields.String()
    file_path = fields.String()
    created_date = fields.Integer()

class UserSchema(Schema):
    id = fields.String()
    email = fields.String()
    phone = fields.String()
    gender = fields.Boolean()
    full_name = fields.String()
    birthday = fields.Date()
    address = fields.Dict()
    detail_address = fields.String()
    group = fields.Nested(GroupSchema())
    avatar = fields.Nested(FileSchema())
    created_date = fields.Integer()
    is_active = fields.Boolean()
    status = fields.Boolean()

    join_date = fields.Date()
    finish_date = fields.Date()
    identification_card = fields.String()
    tax_code = fields.String()
    social_insurance_number = fields.String()
    number_dependent = fields.Integer()
    ethnicity = fields.String()
    nationality = fields.String()



class StatisticTop10CustomerSchema(Schema):
    id = fields.Str()
    full_name = fields.Str()
    email = fields.Str()
    avatar = fields.Str()  # Đường dẫn avatar đã lấy từ Files.file_path
    total_count = fields.Int()


class StatisticTop5ProductSchema(Schema):
    id = fields.Str()
    name = fields.Str()
    file_path = fields.Str()  # Đường dẫn avatar đã lấy từ Files.file_path
    total_quantity = fields.Int()



class AuthValidation(BaseValidation):
    password = fields.String(
        required=True,
        validate=[
            validate.Length(min=8, max=16, error="Mật khẩu phải từ 8 đến 16 ký tự.")
        ],
        error_messages={"required": "Mật khẩu không được để trống."}
    )

    email = fields.String(
        required=True,
        validate=[
            validate.Length(min=8, max=100, error="Email phải từ 8 đến 100 ký tự."),
            validate.Regexp(REGEX_EMAIL, error="Email không hợp lệ.")
        ],
        error_messages={"required": "Email không được để trống."})


class PasswordValidation(BaseValidation):
    current_password = fields.String(
        required=True,
        error_messages={"required": "Mật khẩu hiện tại không được để trống."}
    )

    new_password = fields.String(
        required=True,
        validate=[validate.Length(min=8, max=16, error="Mật khẩu mới phải từ 8 đến 16 ký tự.")],
        error_messages={"required": "Mật khẩu mới không được để trống."}
    )

    confirm_password = fields.String(
        required=True,
        validate=[validate.Length(min=8, max=16, error="Xác nhận mật khẩu phải từ 8 đến 16 ký tự.")],
        error_messages={"required": "Xác nhận mật khẩu không được để trống."}
    )

class RegisterValidation(BaseValidation):
    full_name = fields.String(required=True, error_messages={"required": "Họ và tên không được để trống."})

    password = fields.String(
        required=True,
        validate=[validate.Length(min=8, max=16, error="Mật khẩu phải có độ dài từ 8 đến 16 ký tự.")],
        error_messages={"required": "Mật khẩu không được để trống."}
    )

    confirm_password = fields.String(
        required=True,
        validate=[validate.Length(min=8, max=16, error="Xác nhận mật khẩu phải có độ dài từ 8 đến 16 ký tự.")],
        error_messages={"required": "Xác nhận mật khẩu không được để trống."}
    )

    email = fields.String(
        required=True,
        validate=[
            validate.Length(min=8, max=100, error="Email phải có từ 8 đến 100 ký tự."),
            validate.Regexp(REGEX_EMAIL, error="Email không hợp lệ.")
        ],
        error_messages={"required": "Email không được để trống."}
    )

    phone = fields.String(
        required=True,
        validate=[
            validate.Length(min=10, max=20, error="Số điện thoại phải có từ 10 đến 20 số."),
            validate.Regexp(REGEX_PHONE_NUMBER, error="Số điện thoại không hợp lệ.")
        ],
        error_messages={"required": "Số điện thoại không được để trống."}
    )

    birthday = fields.String(
        required=True,
        error_messages={"required": "Ngày sinh không được để trống."}
    )

class UserValidation(BaseValidation):
    email = fields.String(allow_none=True)
    phone = fields.String(allow_none=True,
                          validate=[validate.Length(min=10, max=20), validate.Regexp(REGEX_PHONE_NUMBER)])
    full_name = fields.String(allow_none=True)
    gender = fields.Boolean(allow_none=True)
    birthday = fields.String(allow_none=True)
    detail_address = fields.String(allow_none=True)
    address = fields.Dict(allow_none=True)

class CartValidation(BaseValidation):
    quantity = fields.Integer(
        required=True,
        error_messages={"required": "Số lượng không được để trống."}
    )

    color_id = fields.String(
        required=True,
        error_messages={"required": "Màu sắc không được để trống."}
    )

    size_id = fields.String(
        required=True,
        error_messages={"required": "Kích thước không được để trống."}
    )

    product_id = fields.String(
        required=True,
        error_messages={"required": "Mã sản phẩm không được để trống."}
    )

class CartUpdateValidation(BaseValidation):
    quantity = fields.Integer(
        required=True,
        error_messages={"required": "Số lượng không được để trống."}
    )

    color_id = fields.String(
        required=True,
        error_messages={"required": "Mã màu không được để trống."}
    )

    size_id = fields.String(
        required=True,
        error_messages={"required": "Mã kích thước không được để trống."}
    )

    product_id = fields.String(
        required=True,
        error_messages={"required": "Mã sản phẩm không được để trống."}
    )


class ReactionValidation(BaseValidation):
    category = fields.String(
        required=True,
        validate=validate.OneOf(
            [TYPE_REACTION.get('ARTICLE', "article"), TYPE_REACTION.get('COMMENT', "comment")],
            error="Danh mục phải là 'article' hoặc 'comment'."
        ),
        error_messages={"required": "Danh mục phản ứng không được để trống."}
    )

    reactable_id = fields.String(
        required=True,
        error_messages={"required": "ID phản ứng không được để trống."}
    )


class TypeProductValidation(BaseValidation):
    key = fields.String(
        required=True,
        error_messages={"required": "Mã sản phẩm không được để trống."}
    )

    name = fields.String(
        required=True,
        error_messages={"required": "Tên sản phẩm không được để trống."}
    )

    type_id = fields.String(
        allow_none=True
    )

class ProductValidation(BaseValidation):
    files = fields.List(
        fields.Dict(
            keys=fields.Str(),
            values=fields.Raw(),
            validate=validate.Length(min=1, error="Dữ liệu tệp tin không được rỗng.")
        ),
        required=True,
        validate=validate.Length(min=1, error="Danh sách tệp tin phải chứa ít nhất một mục."),
        error_messages={"required": "Danh sách tệp tin không được để trống."}
    )

    sizes = fields.List(
        fields.String(validate=validate.Length(min=1, error="Kích thước không được rỗng.")),
        required=True,
        validate=validate.Length(min=1, error="Phải chọn ít nhất một kích thước."),
        error_messages={"required": "Danh sách kích thước không được để trống."}
    )

    colors = fields.List(
        fields.String(validate=validate.Length(min=1, error="Màu sắc không được rỗng.")),
        required=True,
        validate=validate.Length(min=1, error="Phải chọn ít nhất một màu sắc."),
        error_messages={"required": "Danh sách màu sắc không được để trống."}
    )

    original_price = fields.Float(
        required=True,
        error_messages={"required": "Giá gốc không được để trống."}
    )

    discount = fields.Integer(
        allow_none=True,
        default=0,
        validate=validate.Range(min=0, max=100, error="Giảm giá phải từ 0 đến 100%."),
        error_messages={"invalid": "Giảm giá phải là một số nguyên."}
    )

    discount_from_date = fields.Integer(
        allow_none=True
    )

    discount_to_date = fields.Integer(
        allow_none=True
    )

    name = fields.String(
        required=True,
        error_messages={"required": "Tên sản phẩm không được để trống."}
    )

    describe = fields.String(
        allow_none=True
    )

    type_product_id = fields.String(
        required=True,
        error_messages={"required": "Mã loại sản phẩm không được để trống."}
    )

class StaffValidation(BaseValidation):
    email = fields.String(
        required=True,
        validate=validate.Regexp(REGEX_EMAIL, error="Email không hợp lệ."),
        error_messages={"required": "Email không được để trống."}
    )

    phone = fields.String(
        required=True,
        validate=[
            validate.Length(min=10, max=20, error="Số điện thoại phải có độ dài từ 10 đến 20 ký tự."),
            validate.Regexp(REGEX_PHONE_NUMBER, error="Số điện thoại không hợp lệ.")
        ],
        error_messages={"required": "Số điện thoại không được để trống."}
    )

    full_name = fields.String(
        required=True,
        error_messages={"required": "Họ và tên không được để trống."}
    )

    gender = fields.Boolean(
        required=True,
        error_messages={"required": "Giới tính không được để trống."}
    )

    birthday = fields.String(
        required=True,
        error_messages={"required": "Ngày sinh không được để trống."}
    )

    detail_address = fields.String(
        required=True,
        error_messages={"required": "Địa chỉ chi tiết không được để trống."}
    )

    address = fields.Dict(
        required=True,
        error_messages={"required": "Địa chỉ không được để trống."}
    )

    join_date = fields.String(
        required=True,
        error_messages={"required": "Ngày vào công ty không được để trống."}
    )

    finish_date = fields.String(
        allow_none=True
    )

    tax_code = fields.String(
        required=True,
        error_messages={"required": "Mã số thuế không được để trống."}
    )

    identification_card = fields.String(
        required=True,
        error_messages={"required": "CMND/CCCD không được để trống."}
    )

    number_dependent = fields.Integer(
        required=True,
        error_messages={"required": "Số người phụ thuộc không được để trống."}
    )

    nationality = fields.String(
        required=True,
        error_messages={"required": "Quốc tịch không được để trống."}
    )

    ethnicity = fields.String(
        required=True,
        error_messages={"required": "Dân tộc không được để trống."}
    )

    social_insurance_number = fields.Integer(
        required=True,
        error_messages={"required": "Số bảo hiểm xã hội không được để trống."}
    )

    group_id = fields.String(
        required=True,
        error_messages={"required": "Mã nhóm không được để trống."}
    )

    avatar_id = fields.String(
        allow_none=True
    )


class AttendanceSchema(Schema):
    id = fields.String()
    user = fields.Nested(UserSchema(only=("id","full_name")))
    work_date = fields.Date()  # Ngày làm việc
    check_in = fields.Time(format="%H:%M")  # Định dạng giờ check-in
    check_out = fields.Time(format="%H:%M")  # Định dạng giờ check-out
    work_unit = fields.String()
    status = fields.String()


class PaymentValidation(BaseValidation):
    message = fields.String(allow_none=True)

    ship_id = fields.String(
        required=True,
        error_messages={"required": "Mã đơn vị vận chuyển không được để trống."}
    )

    address_order_id = fields.String(
        required=True,
        error_messages={"required": "Mã địa chỉ đặt hàng không được để trống."}
    )

    payment_type = fields.String(
        required=True,
        validate=validate.OneOf(
            choices=TYPE_PAYMENT_ONLINE.values(),
            error="Loại thanh toán chỉ được là 'momo' hoặc 'zalo'."
        ),
        error_messages={"required": "Loại thanh toán không được để trống."}
    )

class SessionOrderValidate(BaseValidation):
    message = fields.String(
        allow_none=True
    )

    ship_id = fields.String(
        required=True,
        error_messages={"required": "Mã đơn vị vận chuyển không được để trống."}
    )

    address_order_id = fields.String(
        required=True,
        error_messages={"required": "Địa chỉ nhận hàng không được để trống."}
    )

    payment_type = fields.String(
        required=True,
        validate=validate.OneOf(
            choices=TYPE_PAYMENT.values(),
            error="Hình thức thanh toán phải là 'cod', 'momo' hoặc 'zalo'."
        ),
        error_messages={"required": "Hình thức thanh toán không được để trống."}
    )

    payment_online_id = fields.String(
        allow_none=True
    )

    @validates_schema
    def validate_payment_online_id(self, data, **kwargs):
        if data.get('payment_type') in TYPE_PAYMENT_ONLINE.values() and not data.get('payment_online_id'):
            raise ValidationError("Mã giao dịch thanh toán online bắt buộc khi phương thức thanh toán là 'momo' hoặc 'zalo'.",
                                  field_name='payment_online_id')


class ArticleValidate(BaseValidation):
    tags = fields.List(
        fields.String(),
    )

    title = fields.String(
        required=True,
        error_messages={"required": "Tiêu đề không được để trống."}
    )

    community_id = fields.String(
        required=True,
        error_messages={"required": "Mã cộng đồng không được để trống."}
    )

    body = fields.String(
        required=True,
        error_messages={"required": "Nội dung bài viết không được để trống."}
    )


class CommentValidation(BaseValidation):
    body = fields.String(
        required=True,
        error_messages={"required": "Nội dung bình luận không được để trống."}
    )

    article_id = fields.String(
        required=True,
        error_messages={"required": "Mã bài viết không được để trống."}
    )

    ancestry_id = fields.String(
        allow_none=True
    )

    mention_usernames = fields.List(
        fields.String,
        allow_none=True
    )


class ReportValidation(BaseValidation):
    files = fields.List(
        fields.Dict(
            keys=fields.Str(),
            values=fields.Raw(),
        ),
        allow_none=True
    )

    order_id = fields.String(
        required=True,
        error_messages={"required": "Mã đơn hàng không được để trống."}
    )

    reason = fields.String(
        required=True,
        error_messages={"required": "Lý do báo cáo không được để trống."}
    )

    message = fields.String(
        required=True,
        error_messages={"required": "Nội dung báo cáo không được để trống."}
    )

class TypeProductSchema(Schema):
    id = fields.String()
    key = fields.String()
    name = fields.String()
    created_date = fields.Integer()
    modified_date = fields.Integer()

class TypeProductWithChildrenSchema(TypeProductSchema):
    type_child = fields.List(fields.Nested(TypeProductSchema))


class ColorOrSizeSchema(Schema):
    id = fields.String()
    name = fields.String()
    index = fields.Integer()
    created_date = fields.Integer()




class ProductSchema(Schema):
    id = fields.String()
    original_price = fields.Integer()
    discount = fields.Integer()
    name = fields.String()
    describe = fields.String()
    type_product = fields.Nested(TypeProductSchema)
    colors = fields.List(fields.Nested(ColorOrSizeSchema))
    sizes = fields.List(fields.Nested(ColorOrSizeSchema))
    files = fields.List(fields.Nested(FileSchema()))
    created_date = fields.Integer()
    modified_date = fields.Integer()
    discount_from_date = fields.Integer()
    discount_to_date = fields.Integer()
    detail = fields.Dict()

    class Meta:
        ordered = True

class QueryParamsSchema(BaseValidation):
    from_money = fields.Integer(allow_none=True, validate=validate.Range(min=0))  # Có thể None, không nhỏ hơn 0
    to_money = fields.Integer(allow_none=True, validate=validate.Range(min=0))  # Có thể None, nhưng không nhỏ hơn 0
    from_date = fields.Integer(allow_none=True, validate=validate.Range(min=0))  # Có thể None, không nhỏ hơn 0
    to_date = fields.Integer(allow_none=True, validate=validate.Range(min=0))
    page = fields.Integer(required=True, validate=validate.Range(min=1))  # Bắt buộc, không nhỏ hơn 1
    page_size = fields.Integer(missing=10, validate=validate.Range(min=1, max=100))  # Mặc định là 10, giới hạn tối đa 100
    order_by = fields.String(missing="created_date")  # Mặc định là 'created_date'
    sort = fields.String(
        missing="desc", validate=validate.OneOf(["asc", "desc"])  # Chỉ chấp nhận 'asc' hoặc 'desc'
    )
    text_search = fields.String(allow_none=True)  # Có thể None
    select_type = fields.List(fields.String(), allow_none=True)

    @pre_load
    def parse_select_type(self, data, **kwargs):
        """Tự động convert select_type từ string JSON thành list"""
        if "select_type" in data and isinstance(data["select_type"], str):
            try:
                data["select_type"] = json.loads(data["select_type"])
            except json.JSONDecodeError:
                raise ValidationError({"select_type": "Invalid JSON format."})
        return data

    @pre_load
    def normalize_empty_strings_and_trim(self, data, **kwargs):
        for key in ['text_search', 'type_id', 'from_money', 'to_money']:
            if key in data:
                value = data[key]
                if isinstance(value, str):
                    value = value.strip()
                    data[key] = value if value != '' else None
        return data

class QueryParamsAllSchema(BaseValidation):
    page = fields.Integer(required=True, validate=validate.Range(min=1))  # Bắt buộc, không nhỏ hơn 1
    page_size = fields.Integer(missing=10, validate=validate.Range(min=1, max=100))  # Mặc định là 10, giới hạn tối đa 100
    order_by = fields.String(missing="created_date")  # Mặc định là 'created_date'
    sort = fields.String(
        missing="desc", validate=validate.OneOf(["asc", "desc"])  # Chỉ chấp nhận 'asc' hoặc 'desc'
    )
    text_search = fields.String(allow_none=True)  # Có thể None

class QueryTimeSheetSchema(QueryParamsAllSchema):
    time_str=fields.String(allow_none=True)

class ParamTypeProduct(QueryParamsAllSchema):
    type_id = fields.String(allow_none=True)

class QueryParamsArticleSchema(QueryParamsAllSchema):
    community_id = fields.String(allow_none=True)
    timestamp = fields.Integer(allow_none=True)
    profile_id = fields.String(allow_none=True)
    product_id = fields.String(allow_none=True)


class CommentParamsValidation(BaseValidation):
    page = fields.Integer()
    page_size = fields.Integer(missing=10,
                               validate=validate.Range(min=1, max=100))  # Mặc định là 10, giới hạn tối đa 100
    order_by = fields.String(missing="created_date", validate=validate.OneOf(["created_date", "vote"]))
    sort = fields.String(
        missing="desc", validate=validate.OneOf(["asc", "desc"])  # Chỉ chấp nhận 'asc' hoặc 'desc'
    )


class QueryParamsOrderSchema(BaseValidation):
    page = fields.Integer(required=True, validate=validate.Range(min=1))  # Bắt buộc, không nhỏ hơn 1
    page_size = fields.Integer(missing=10, validate=validate.Range(min=1, max=100))  # Mặc định là 10, giới hạn tối đa 100
    order_by = fields.String(missing="created_date")  # Mặc định là 'created_date'
    sort = fields.String(
        missing="desc", validate=validate.OneOf(["asc", "desc"])  # Chỉ chấp nhận 'asc' hoặc 'desc'
    )
    status = fields.String(validate=validate.OneOf(["pending", "processing", "delivering", "resolved"]))
    text_search = fields.String(allow_none=True)
    time = fields.String()

class ParamsReportSchema(BaseValidation):
    page = fields.Integer(required=True, validate=validate.Range(min=1))  # Bắt buộc, không nhỏ hơn 1
    page_size = fields.Integer(missing=10,
                               validate=validate.Range(min=1, max=100))  # Mặc định là 10, giới hạn tối đa 100
    order_by = fields.String(missing="created_date")  # Mặc định là 'created_date'
    sort = fields.String(
        missing="desc", validate=validate.OneOf(["asc", "desc"])  # Chỉ chấp nhận 'asc' hoặc 'desc'
    )
    status = fields.String(allow_none=True, validate=validate.OneOf(["pending", "processing", "delivering", "resolved"]))
    text_search = fields.String(allow_none=True)
    created_at = fields.String(allow_none=True)


class QueryNotifyParamsSchema(BaseValidation):
    notify_unread = fields.Boolean(allow_none=True, missing=False)
    page = fields.Integer(required=True, validate=validate.Range(min=1))  # Bắt buộc, không nhỏ hơn 1
    page_size = fields.Integer(missing=10, validate=validate.Range(min=1, max=100))


class LastSeenNotifyParamsSchema(BaseValidation):
    last_time = fields.Integer()


# Mặc định là 10, giới hạn tối đa 100

class QueryParamsManageOrderSchema(QueryParamsOrderSchema):
    time = fields.String()

class CartSchema(Schema):
    id = fields.String()
    product = fields.Nested(ProductSchema(only=("id", "original_price", "discount", "name", "colors", "sizes",
                                                "describe", "files", "discount_to_date", "detail", "type_product")))
    color = fields.Nested(ColorOrSizeSchema)
    size = fields.Nested(ColorOrSizeSchema)
    created_date = fields.Integer()
    modified_date = fields.Integer()
    quantity = fields.Integer()


class CartDetailSchema(Schema):
    id = fields.String()
    product = fields.Nested(ProductSchema(only=("id", "original_price", "discount", "name",
                                                "files", "discount_to_date", "detail")))
    color = fields.Nested(ColorOrSizeSchema)
    size = fields.Nested(ColorOrSizeSchema)
    quantity = fields.Integer()


class SessionOrderCartItemSchema(Schema):
    id = fields.String()
    index = fields.Integer()
    cart_detail = fields.Nested(CartDetailSchema(only=("id", "product", "color", "size", "quantity")))

class SessionSchema(Schema):
    id = fields.String()
    items = fields.List(fields.Nested(SessionOrderCartItemSchema))
    created_date = fields.Integer()
    duration = fields.Integer()

class AddressOrderSchema(Schema):
    id = fields.String()
    address = fields.Dict()
    detail_address = fields.String()
    index = fields.Integer()
    default = fields.Boolean()
    full_name = fields.String()
    phone = fields.String()

class OrderItemSchema(Schema):
    id = fields.String()
    product = fields.Nested(ProductSchema(only=("id","name", "files", "type_product", "detail")))
    color = fields.Nested(ColorOrSizeSchema)
    size = fields.Nested(ColorOrSizeSchema)
    created_date = fields.Integer()
    count = fields.Float()
    quantity = fields.Integer()

class PaymentOnlineSchema(Schema):
    id = fields.String()
    type = fields.String()

class OrderSchema(Schema):
    id = fields.String()
    full_name = fields.String()
    phone_number = fields.String()
    detail_address = fields.String()
    address = fields.Dict()
    count = fields.Float()
    created_date = fields.Integer()
    message = fields.String()
    price_ship = fields.Float()
    status = fields.String()
    items = fields.List(fields.Nested(OrderItemSchema))
    payment_status = fields.Boolean()
    payment_online = fields.Nested(PaymentOnlineSchema)
    is_paid = fields.Boolean()
    user = fields.Nested(UserSchema(only=("id","email", "full_name")))


class NotifySchema(Schema):
    id = fields.String()
    created_date = fields.Integer()
    modified_date = fields.Integer()
    notify_type = fields.String()
    unread = fields.Boolean()
    detail = fields.Dict()



class CommunitySchema(Schema):
    id = fields.String()
    name = fields.String()
    description = fields.String()

class DocumentSchema(Schema):
    id = fields.String()
    name = fields.String()

class DocumentStaff(Schema):
    id = fields.String()
    user = fields.Nested(UserSchema(only=("id","email", "full_name")))
    document = fields.Nested(DocumentSchema)
    file = fields.Nested(FileSchema())

class ArticleTagProductSchema(Schema):
    id = fields.String()
    product = fields.Nested(ProductSchema(only=("id", "name", "files")))
    index = fields.Integer()

class ArticleSchema(Schema):
    id = fields.String()
    title = fields.String()
    body = fields.String()
    user_id = fields.String()
    body_type = fields.String()
    created_date = fields.Integer()
    modified_date = fields.Integer()
    user = fields.Nested(UserSchema(only=("id","full_name", "avatar")))
    community = fields.Nested(CommunitySchema(only=("id","name")))
    has_reacted = fields.Method("get_has_reacted")
    reaction_count = fields.Integer()
    tag_product = fields.Nested(ArticleTagProductSchema, many=True)
    def get_has_reacted(self, article):
        # Lấy user_id từ context (nếu có)
        user_id = self.context.get("user_id")
        if not user_id:
            return False

        # Kiểm tra nếu người dùng đã react
        reaction = Reaction.query.filter_by(
            reactable_id=article.id,
            user_id=user_id,
            category=TYPE_REACTION.get('ARTICLE')
        ).first()

        if reaction:
            return bool(reaction.vote)

        return False


class CommentSchema(Schema):
    id = fields.String()
    body = fields.String()
    created_date = fields.Integer()
    modified_date = fields.Integer()
    ancestry_id = fields.String()
    user = fields.Nested(UserSchema(only=("id","full_name", "avatar")))
    article = fields.Nested(ArticleSchema(only=("id", "title")))
    has_reacted = fields.Method("get_has_reacted")
    reaction_count = fields.Integer()
    reply_count = fields.Integer()
    replies = fields.Method("get_replies")
    def get_replies(self, comment):
        order_by = self.context.get("order_by", "created_date")
        sort = self.context.get("sort", 'desc')
        user_id = self.context.get("user_id")
        depth = self.context.get("depth", 0)

        if depth <= 0:
            return []

        column_sorted = getattr(Comment, order_by)
        sorted_replies = comment.replies.order_by(desc(column_sorted)).limit(2) if sort == "desc" else comment.replies.order_by(asc(column_sorted)).limit(2)

        # Serialize replies với độ sâu đệ quy
        schema = CommentSchema(
            many=True,
            context={"order_by": order_by, "sort": sort, "depth": depth - 1, "user_id": user_id}
        )
        return schema.dump(sorted_replies)

    def get_has_reacted(self, comment):
        # Lấy user_id từ context (nếu có)
        user_id = self.context.get("user_id")
        if not user_id:
            return False

        # Kiểm tra nếu người dùng đã react
        reaction = Reaction.query.filter_by(
            reactable_id=comment.id,
            user_id=user_id,
            category=TYPE_REACTION.get('COMMENT')
        ).first()

        if reaction:
            return bool(reaction.vote)

        return False



class OrderReportSchema(Schema):
    id = fields.String()
    reason = fields.String()
    message = fields.String()
    files = fields.List(fields.Nested(FileSchema()))
    created_date = fields.Integer()
    result_date = fields.Integer()
    result = fields.String()
    status = fields.String()
    user = fields.Nested(UserSchema(only=("id","full_name", "avatar", "email", "phone")))
    order = fields.Nested(OrderSchema())
class RegionSchema(Schema):
    id = fields.String()
    name = fields.String()

class PriceShipSchema(Schema):
    id = fields.String()
    price = fields.Integer()
    shipper_id = fields.String()
    region = fields.Nested(RegionSchema())

class ShipperSchema(Schema):
    id = fields.String()
    name = fields.String()
    index = fields.Integer()
    price_ship = fields.List(fields.Nested(PriceShipSchema()))

class PaymentOnlineSchema(Schema):
    id = fields.String()
    order_payment_id = fields.String()
    request_payment_id = fields.String()
    session_order_id = fields.String()
    result_payment = fields.Dict(allow_none=True)
    status_payment = fields.Boolean()
    type = fields.String()
    created_date = fields.Integer()
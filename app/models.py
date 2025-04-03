# coding: utf-8
from datetime import time, timedelta, datetime
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, TEXT, asc, desc, func
from sqlalchemy.orm import validates

from app.enums import DURATION_SESSION_MINUTES, TYPE_REACTION, STATUS_ORDER, ATTENDANCE, \
    ATTENDANCE_STATUS, WORK_UNIT_TYPE, CONTENT_TYPE, NOTIFY_TYPE
from app.extensions import db
from app.utils import get_timestamp_now


class Address(db.Model):
    __tablename__ = 'address'
    id = db.Column(db.String(50), primary_key=True)
    province = db.Column(db.Text(collation='utf8mb4_unicode_ci'), nullable=True)
    district = db.Column(db.Text(collation='utf8mb4_unicode_ci'), nullable=True)
    ward = db.Column(db.Text(collation='utf8mb4_unicode_ci'), nullable=True)


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.String(50), primary_key=True)
    email = db.Column(db.String(100, collation="utf8mb4_vietnamese_ci"), nullable=False)
    phone = db.Column(db.String(50))
    password = db.Column(db.String(255), nullable=False)
    gender = db.Column(db.Boolean, default=0, nullable=False) #0: Nữ, # 1: Nam
    full_name = db.Column(db.String(100, collation="utf8mb4_vietnamese_ci"), nullable=False)
    avatar_id = db.Column(db.String(50), db.ForeignKey('files.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    avatar = db.relationship("Files", viewonly=True)

    birthday = db.Column(db.DATE, nullable=False)
    created_date = db.Column(INTEGER(unsigned=True), default=get_timestamp_now(), index=True)
    modified_date = db.Column(INTEGER(unsigned=True), default=get_timestamp_now())
    is_deleted = db.Column(db.Boolean, default=0)
    is_active = db.Column(db.Boolean, default=0)  # 1: Mở tài khoản , 0: Khóa tài khoản
    status = db.Column(db.Boolean, default=1)  # 1: Kích hoạt, 0: Không kích hoạt

    address_id = db.Column(ForeignKey('address.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    detail_address = db.Column(db.String(100, collation="utf8mb4_vietnamese_ci"), nullable=True)
    last_seen_notify = db.Column(INTEGER(unsigned=True), nullable=True)
    group_id = db.Column(ForeignKey('group.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    group = relationship('Group', viewonly=True)

    # nhan vien
    identification_card = db.Column(db.String(100), nullable=True) # can cuoc cong dan
    tax_code = db.Column(db.String(100, collation="utf8mb4_vietnamese_ci"), nullable=True) # ma so thue
    social_insurance_number = db.Column(db.String(100, collation="utf8mb4_vietnamese_ci"), nullable=True) # Mã BHXH
    join_date = db.Column(db.DATE, nullable=True)
    finish_date = db.Column(db.DATE, nullable=True)
    number_dependent = db.Column(INTEGER(unsigned=True), default=0) # người phụ thuộc
    ethnicity = db.Column(db.String(100, collation="utf8mb4_vietnamese_ci"), nullable=True) # Dan toc
    nationality = db.Column(db.String(100, collation="utf8mb4_vietnamese_ci"), nullable=True) # Quoc Tich

    attendances = db.relationship('Attendance', back_populates='user', cascade="all, delete-orphan")
    latest_salary = db.relationship(
        'Salary',
        primaryjoin="and_(User.id == Salary.user_id)",
        order_by="desc(Salary.created_date)",
        uselist=False
    )

    @property
    def address(self):
        data = {
            'province': '',
            'district': '',
            'ward': ''
        }
        address = Address.query.filter_by(id=self.address_id).first()
        if address:
            data['province'] = address.province
            data['district'] = address.district
            data['ward'] = address.ward
        return data


class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.String(50), primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    user = db.relationship('User', back_populates='attendances')

    work_date = db.Column(db.Date, nullable=False)
    check_in = db.Column(db.Time, nullable=True)
    check_out = db.Column(db.Time, nullable=True)

    @property
    def work_unit(self):
        if self.check_in and self.check_out:
            # Chọn một ngày cơ sở (ví dụ: ngày hôm nay)
            base_date = datetime.today().date()
            # Chuyển đổi check_in và check_out của nhân viên thành datetime
            check_in_dt = datetime.combine(base_date, self.check_in)
            check_out_dt = datetime.combine(base_date, self.check_out)
            # Chuyển đổi thời gian của ATTENDANCE thành datetime
            check_in_attendance = datetime.combine(base_date, ATTENDANCE['CHECK_IN'])
            check_out_attendance = datetime.combine(base_date, ATTENDANCE['CHECK_OUT'])

            # Điều kiện trả về "full"
            if check_in_dt <= check_in_attendance and check_out_dt >= check_out_attendance:
                return WORK_UNIT_TYPE.get('FULL')

            elif check_in_dt <= (check_in_attendance + timedelta(hours=1)) and check_out_dt >= (
                    check_out_attendance - timedelta(hours=1)):
                return WORK_UNIT_TYPE.get('HALF')
        return None

    @property
    def status(self):
        if self.check_in:
            if self.check_out:
                if self.work_unit == WORK_UNIT_TYPE.get('FULL'):
                    return ATTENDANCE_STATUS['PRESENT']
                elif self.work_unit == WORK_UNIT_TYPE.get('HALF', 'half'):
                    return ATTENDANCE_STATUS['MISSING']
                else:
                    return ATTENDANCE_STATUS['ABSENT']

            else:
                return ATTENDANCE_STATUS['ABSENT']

        return ATTENDANCE_STATUS['ACCEPTABLE_ABSENT']


class Salary(db.Model):
    __tablename__ = 'salary'

    id = db.Column(db.String(50), primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'),
                           nullable=False)
    base_salary = db.Column(db.Numeric(10, 2), nullable=False)
    kpi_salary = db.Column(INTEGER(unsigned=True))
    allowance_salary = db.Column(INTEGER(unsigned=True))
    created_date = db.Column(INTEGER(unsigned=True), default=get_timestamp_now(), index=True)

class SalaryReport(db.Model):
    __tablename__ = 'salary_report'

    id = db.Column(db.String(50), primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    salary_id = db.Column(ForeignKey('salary.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)

    user = db.relationship('User', viewonly=True)
    salary = relationship('Salary', viewonly=True)

    payment_date = db.Column(db.Date, nullable=False)

    kpi_score = db.Column(INTEGER(unsigned=True), default=0, nullable=False)
    number_dependent = db.Column(INTEGER(unsigned=True), default=0) # người phụ thuộc
    reward = db.Column(INTEGER(unsigned=True), default=0, nullable=False)

    total_salary = db.Column(db.Numeric(10, 2), nullable=False)

    created_date = db.Column(INTEGER(unsigned=True), default=get_timestamp_now(), index=True)
    modified_date = db.Column(INTEGER(unsigned=True), default=get_timestamp_now())


class DocumentStorage(db.Model):
    __tablename__ = 'document_storage'

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(255, collation="utf8mb4_vietnamese_ci"), nullable=False)# Tên tài liệu
    index = db.Column(db.Integer, nullable=True, default=0)


class StaffDocumentFile(db.Model):
    __tablename__ = 'staff_document_file'
    id = db.Column(db.String(50), primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'),
                        nullable=False)
    user = db.relationship('User', viewonly=True)
    document_id = db.Column(db.String(50), db.ForeignKey('document_storage.id', ondelete='CASCADE', onupdate='CASCADE'),
                        nullable=False)
    document = db.relationship('DocumentStorage', viewonly=True)
    file_id = db.Column(db.String(50), db.ForeignKey('files.id', ondelete='CASCADE', onupdate='CASCADE'),
                        nullable=False)
    file = db.relationship('Files', viewonly=True)
    index = db.Column(db.Integer, nullable=True, default=0)
    created_date = db.Column(INTEGER(unsigned=True), default=get_timestamp_now(), index=True)
    modified_date = db.Column(INTEGER(unsigned=True), default=get_timestamp_now())


class Community(db.Model):
    __tablename__ = 'community'

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(255, collation="utf8mb4_vietnamese_ci"), nullable=False)
    description = db.Column(db.String(255, collation="utf8mb4_vietnamese_ci"))
    created_date = db.Column(INTEGER(unsigned=True), default=get_timestamp_now(), index=True)
    modified_date = db.Column(INTEGER(unsigned=True), default=get_timestamp_now())


class Article(db.Model):
    __tablename__ = 'article'
    id = db.Column(db.String(50), primary_key=True)
    title = db.Column(db.String(150, collation="utf8mb4_vietnamese_ci"), nullable=False)
    body = db.Column(db.Text(collation='utf8mb4_unicode_ci'), nullable=False)
    user_id = db.Column(db.String(50), db.ForeignKey('user.id',
                                                     ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    body_type = db.Column(db.String(50), nullable=True)
    created_date = db.Column(INTEGER(unsigned=True), default=get_timestamp_now(), index=True)
    modified_date = db.Column(INTEGER(unsigned=True), default=get_timestamp_now())
    community_id = db.Column(db.String(50), db.ForeignKey('community.id',
                                                          ondelete='CASCADE', onupdate='CASCADE'), nullable=True)

    @property
    def reaction_count(self):
        return Reaction.query.filter(
            Reaction.reactable_id == self.id, Reaction.category == TYPE_REACTION.get('ARTICLE', "article"),
            Reaction.vote == True).count()

    user = db.relationship('User', viewonly=True)
    community = db.relationship('Community', viewonly=True)


class ArticleTagProduct(db.Model):
    __tablename__ = 'article_tag_product'
    id = db.Column(db.String(50), primary_key=True)
    article_id = db.Column(db.String(50), db.ForeignKey('article.id',
                                                        ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    product_id = db.Column(db.String(50), db.ForeignKey('product.id',
                                                        ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    index = db.Column(db.Integer, nullable=True)


class Reaction(db.Model):
    __tablename__ = 'reaction'
    id = db.Column(db.String(50), primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('user.id',
                                                     ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    reactable_id = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # article, comment
    vote = db.Column(db.Boolean, nullable=False, default=True)
    created_date = db.Column(INTEGER(unsigned=True), default=get_timestamp_now(), index=True)
    modified_date = db.Column(INTEGER(unsigned=True), default=get_timestamp_now())


class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.String(50), primary_key=True)
    body = db.Column(db.Text(collation='utf8mb4_unicode_ci'), nullable=False)
    body_type = db.Column(db.String(50), nullable=True)
    user_id = db.Column(db.String(50), db.ForeignKey('user.id',
                                                     ondelete='CASCADE', onupdate='CASCADE'), nullable=True)

    article_id = db.Column(db.String(50), db.ForeignKey('article.id', ondelete='CASCADE',
                                                        onupdate='CASCADE'), nullable=False)

    ancestry_id = db.Column(db.String(50), db.ForeignKey('comment.id', ondelete='CASCADE', onupdate='CASCADE'))
    created_date = db.Column(INTEGER(unsigned=True), default=get_timestamp_now(), index=True)
    modified_date = db.Column(INTEGER(unsigned=True), default=get_timestamp_now())

    user = db.relationship('User', viewonly=True)
    article = db.relationship('Article', viewonly=True)
    ancestry = db.relationship(
        'Comment',
        remote_side=[id],
        backref=db.backref('replies', lazy='dynamic')
    )

    @property
    def reply_count(self):
        return Comment.query.filter(Comment.ancestry_id == self.id).count()


class AddressOrder(db.Model):
    __tablename__ = 'address_order'

    id = db.Column(db.String(50), primary_key=True)
    address_id = db.Column(ForeignKey('address.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    detail_address = db.Column(db.String(100, collation="utf8mb4_vietnamese_ci"), nullable=True)
    full_name = db.Column(db.String(100, collation="utf8mb4_vietnamese_ci"))
    phone = db.Column(db.String(20))
    user_id = db.Column(db.String(50), db.ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    index = db.Column(db.Integer, nullable=True, default=0)
    default = db.Column(db.Boolean, default=0)

    @property
    def address(self):
        data = {
            'province': '',
            'district': '',
            'ward': ''
        }
        address = Address.query.filter_by(id=self.address_id).first()
        if address:
            data['province'] = address.province
            data['district'] = address.district
            data['ward'] = address.ward
        return data


class Files(db.Model):
    __tablename__ = 'files'

    id = db.Column(db.String(50), primary_key=True)
    file_path = db.Column(db.String(255))
    file_name = db.Column(db.String(255, collation="utf8mb4_vietnamese_ci"), nullable=True)
    created_date = db.Column(INTEGER(unsigned=True), default=get_timestamp_now(), index=True)


class FileLink(db.Model):
    __tablename__ = "file_link"

    # TYPE_FILE_LINK = {
    #     'USER': 'user',
    #     'PRODUCT': 'product',
    #     'ORDER_REPORT': 'order_report',
    # }
    id = db.Column(db.String(50), primary_key=True)
    file_id = db.Column(db.String(50), db.ForeignKey('files.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    table_id = db.Column(db.String(50), nullable=True)
    table_type = db.Column(db.String(50), nullable=False)

    index = db.Column(db.Integer, nullable=True, default=0)
    created_date = db.Column(INTEGER(unsigned=True), default=get_timestamp_now(), index=True)


class Permission(db.Model):
    __tablename__ = 'permission'

    id = db.Column(db.String(50), primary_key=True)
    key = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100, collation="utf8mb4_vietnamese_ci"), nullable=False, unique=False)
    resource = db.Column(db.String(500), nullable=False, unique=False)

class Role(db.Model):
    __tablename__ = 'role'

    id = db.Column(db.String(50), primary_key=True)
    key = db.Column(db.String(100))
    name = db.Column(db.String(100, collation="utf8mb4_vietnamese_ci"), nullable=False, unique=True)
    description = db.Column(db.String(500))
    type = db.Column(db.SmallInteger, default=1)  # tổng của 4 loại quyền sau 1: Xem, 2: Thêm, 4: Sửa, 8: Xóa
    created_date = db.Column(INTEGER(unsigned=True), default=get_timestamp_now())
    modified_date = db.Column(INTEGER(unsigned=True), default=get_timestamp_now())
    group_role = relationship('GroupRole', primaryjoin='GroupRole.role_id == Role.id', viewonly=True)
    role_permission = relationship('RolePermission', primaryjoin='RolePermission.role_id == Role.id', viewonly=True)


class RolePermission(db.Model):
    __tablename__ = 'role_permission'

    id = db.Column(db.String(50), primary_key=True)
    role_id = db.Column(ForeignKey('role.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)
    permission_id = db.Column(ForeignKey('permission.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False,
                              index=True)

    permission = relationship('Permission', primaryjoin='RolePermission.permission_id == Permission.id')
    role = relationship('Role', primaryjoin='RolePermission.role_id == Role.id')


class GroupRole(db.Model):
    __tablename__ = 'group_role'

    id = db.Column(db.String(50), primary_key=True)
    role_id = db.Column(ForeignKey('role.id', ondelete='CASCADE', onupdate='CASCADE'), index=True)
    group_id = db.Column(ForeignKey('group.id', ondelete='CASCADE', onupdate='CASCADE'), index=True)
    role = relationship('Role', primaryjoin='GroupRole.role_id == Role.id')

    @classmethod
    def get_by_id(cls, _id):
        return cls.query.get(_id)


class Group(db.Model):
    __tablename__ = 'group'

    id = db.Column(db.String(50), primary_key=True)
    key = db.Column(db.String(100), unique=True)
    is_staff = db.Column(db.Boolean, nullable=False, default=False)
    is_super_admin = db.Column(db.Boolean, nullable=False, default=False)
    name = db.Column(db.String(100, collation="utf8mb4_vietnamese_ci"), nullable=False, unique=True)
    description = db.Column(db.String(500, collation="utf8mb4_vietnamese_ci"))
    created_date = db.Column(INTEGER(unsigned=True), default=get_timestamp_now(), nullable=False, index=True)
    modified_date = db.Column(INTEGER(unsigned=True), default=0)
    group_roles = relationship('GroupRole', primaryjoin='GroupRole.group_id == Group.id')

    @classmethod
    def get_by_id(cls, _id):
        return cls.query.get(_id)

    @property
    def roles(self):
        return [gr.role for gr in self.group_roles]


class EmailTemplate(db.Model):
    __tablename__ = 'email_template'

    id = db.Column(db.String(50), primary_key=True)
    body = db.Column(TEXT())
    template_code = db.Column(db.String(200))
    object = db.Column(db.JSON)


class VerityCode(db.Model):
    __tablename__ = 'verity_code'

    id = db.Column(db.String(50), primary_key=True)
    code = db.Column(db.String(20))
    user_id = db.Column(db.String(50), db.ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'),
                        nullable=True)


class Region(db.Model):
    __tablename__ = 'region'

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.Text(collation='utf8mb4_unicode_ci'), nullable=True)
    region = db.Column(db.JSON)


class PriceShip(db.Model):
    __tablename__ = 'price_ship'
    id = db.Column(db.String(50), primary_key=True)
    region_id = db.Column(ForeignKey('region.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    shipper_id = db.Column(ForeignKey('shipper.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    price = db.Column(db.Integer, nullable=False)
    region = db.relationship("Region", order_by=Region.name.asc() ,viewonly=True)


class Shipper(db.Model):
    __tablename__ = 'shipper'
    id = db.Column(db.String(50), primary_key=True)
    is_delete = db.Column(db.Boolean, nullable=False, default=False)
    name = db.Column(db.Text(collation='utf8mb4_unicode_ci'), nullable=True)
    index = db.Column(db.Integer, nullable=True, default=0)
    price_ship = db.relationship(
        'PriceShip',
        backref='shipper',
        lazy=True,
        order_by="PriceShip.region_id"  # Sắp xếp theo region_id
    )

class TypeProduct(db.Model):
    __tablename__ = 'type_product'
    id = db.Column(db.String(50), primary_key=True)
    key = db.Column(db.Text)
    name = db.Column(db.Text(collation='utf8mb4_unicode_ci'), nullable=True)
    type_id = db.Column(db.String(50), db.ForeignKey('type_product.id', ondelete='CASCADE', onupdate='CASCADE'),
                        nullable=True)
    created_date = db.Column(INTEGER(unsigned=True), default=get_timestamp_now(), index=True)
    modified_date = db.Column(INTEGER(unsigned=True),default=get_timestamp_now())

    type_child = db.relationship('TypeProduct', backref=db.backref('parent', remote_side=[id]), lazy=True)


class Size(db.Model):
    __tablename__ = 'size'

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.Text(collation='utf8mb4_unicode_ci'), nullable=True)
    product_id = db.Column(db.String(50), db.ForeignKey('product.id', ondelete='CASCADE', onupdate='CASCADE'),
                           nullable=False)
    index = db.Column(db.Integer, nullable=True, default=0)
    created_date = db.Column(INTEGER(unsigned=True), default=get_timestamp_now(), index=True)


class Color(db.Model):
    __tablename__ = 'color'

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.Text(collation='utf8mb4_unicode_ci'), nullable=False)
    product_id = db.Column(db.String(50), db.ForeignKey('product.id', ondelete='CASCADE', onupdate='CASCADE'),
                           nullable=False)
    index = db.Column(db.Integer, nullable=True, default=0)
    created_date = db.Column(INTEGER(unsigned=True), default=get_timestamp_now(), index=True)


class Product(db.Model):
    __tablename__ = 'product'

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.Text(collation='utf8mb4_unicode_ci'), nullable=True)
    describe = db.Column(db.Text(collation='utf8mb4_unicode_ci'), nullable=True)
    type_product_id = db.Column(db.String(50), db.ForeignKey('type_product.id', ondelete='SET NULL',
                                                             onupdate='CASCADE'), nullable=True)
    is_delete = db.Column(db.Boolean, nullable=False, default=False)
    original_price = db.Column(db.BigInteger, nullable=True, default=0)
    discount = db.Column(db.Integer, nullable=True, default=0)
    discount_from_date = db.Column(db.Integer, nullable=True)
    discount_to_date = db.Column(db.Integer, nullable=True)
    type_product = db.relationship('TypeProduct', lazy=True)
    colors = db.relationship('Color', backref='product', lazy=True, order_by="asc(Color.index)")

    sizes = db.relationship('Size', backref='product', lazy=True, order_by="asc(Size.index)")
    created_date = db.Column(db.Integer,
                             default=get_timestamp_now())
    modified_date = db.Column(db.Integer,
                              default=get_timestamp_now())

    files = db.relationship(
        'Files',
        secondary='file_link',
        primaryjoin=(
            "and_(Product.id == FileLink.table_id, FileLink.table_type == 'product')"
        ),
        secondaryjoin="FileLink.file_id == Files.id",
        lazy='dynamic',
        order_by="asc(FileLink.index)",
        viewonly=True
    )

    @property
    def detail(self):
        dict_data = {
            "has_sale": False,
            "original_price": self.original_price,
            "price": self.original_price,
            "discount": 0
        }
        if (self.discount_from_date and self.discount_to_date and self.discount > 0
                and (self.discount_to_date > get_timestamp_now() > self.discount_from_date)):
            dict_data["has_sale"] = True
            dict_data["price"] = int(self.original_price * (100 - self.discount) / 100)
            dict_data["discount"] = self.discount

        return dict_data


class DiscountCoupon(db.Model):
    __tablename__ = 'discount_coupon'

    id = db.Column(db.String(50), primary_key=True)  # Coupon ID
    discount_value = db.Column(db.Float, nullable=False)
    discount_limit = db.Column(db.Integer, nullable=True)
    expiration_date = db.Column(db.Integer, default=get_timestamp_now())
    order_price_from = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    used_count = db.Column(db.Integer, default=0)

    created_date = db.Column(db.Integer,
                             default=get_timestamp_now())
    modified_date = db.Column(db.Integer,
                              default=get_timestamp_now())


class CartItems(db.Model):
    __tablename__ = 'cart_items'
    id = db.Column(db.String(50), primary_key=True)

    quantity = db.Column(db.Integer, nullable=True, default=1)
    color_id = db.Column(db.String(50), db.ForeignKey('color.id', ondelete='SET NULL', onupdate='CASCADE'),
                         nullable=True)
    size_id = db.Column(db.String(50), db.ForeignKey('size.id', ondelete='SET NULL', onupdate='CASCADE'),
                        nullable=True)
    created_date = db.Column(db.Integer, default=get_timestamp_now())
    modified_date = db.Column(db.Integer, default=get_timestamp_now())
    user_id = db.Column(db.String(50), db.ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'),
                        nullable=True)
    product_id = db.Column(db.String(50), db.ForeignKey('product.id', ondelete='CASCADE', onupdate='CASCADE'),
                           nullable=True)
    product = db.relationship("Product", viewonly=True)
    color = db.relationship("Color", viewonly=True)
    size = db.relationship("Size", viewonly=True)


class SessionOrderCartItems(db.Model):
    __tablename__ = 'session_order_cart_items'
    id = db.Column(db.String(50), primary_key=True)
    index = db.Column(db.Integer, nullable=False, default=0)
    cart_id = db.Column(db.String(50), db.ForeignKey('cart_items.id', ondelete='CASCADE',
                                                     onupdate='CASCADE'), nullable=False)
    session_order_id = db.Column(db.String(50), db.ForeignKey('session_order.id', ondelete='CASCADE',
                                                              onupdate='CASCADE'), nullable=False)

    cart_detail = relationship('CartItems')


class SessionOrder(db.Model):
    __tablename__ = 'session_order'

    id = db.Column(db.String(50), primary_key=True)
    created_date = db.Column(db.Integer, default=get_timestamp_now())
    user_id = db.Column(db.String(50), db.ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'),
                        nullable=True)
    duration = db.Column(db.Integer, default=lambda: get_timestamp_now() + DURATION_SESSION_MINUTES * 60)
    items = db.relationship('SessionOrderCartItems', lazy=True,
                            order_by="asc(SessionOrderCartItems.index)")

    is_delete = db.Column(db.Boolean, default=False)


class Orders(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.String(50), primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'),
                        nullable=True)
    full_name = db.Column(db.String(100, collation="utf8mb4_vietnamese_ci"))
    phone_number = db.Column(db.String(100), nullable=True)
    address_id = db.Column(ForeignKey('address.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True,
                           index=True)
    detail_address = db.Column(db.String(100, collation="utf8mb4_vietnamese_ci"))
    count = db.Column(db.BigInteger, nullable=True, default=0)
    created_date = db.Column(db.Integer, default=get_timestamp_now())
    modified_date = db.Column(db.Integer, default=get_timestamp_now())
    message = db.Column(db.Text(collation='utf8mb4_unicode_ci'), nullable=True)
    ship_id = db.Column(db.String(50), db.ForeignKey('shipper.id', ondelete='SET NULL', onupdate='SET NULL'),
                        nullable=True)
    price_ship = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), default='pending')
    items = db.relationship('OrderItems', lazy=True,
                            order_by="asc(OrderItems.created_date)")
    payment_status = db.Column(db.Boolean, nullable=False, default=False) # Thanh toán online hay tiền mặt
    payment_online_id = db.Column(db.String(50), db.ForeignKey('payment_online.id', ondelete='SET NULL', onupdate='SET NULL'))

    payment_online = db.relationship("PaymentOnline", viewonly=True)
    user = db.relationship('User', viewonly=True)

    @property
    def is_paid(self):
        if self.payment_status and self.payment_online_id:
            return True
        if self.status == STATUS_ORDER.get("RESOLVED"):
            return True
        return False

    @property
    def address(self):
        data = {
            'province': '',
            'district': '',
            'ward': ''
        }
        address = Address.query.filter_by(id=self.address_id).first()
        if address:
            data['province'] = address.province
            data['district'] = address.district
            data['ward'] = address.ward
        return data


class Notify(db.Model):
    __tablename__ = 'notify'

    id = db.Column(db.String(50), primary_key=True)
    created_date = db.Column(db.Integer, default=get_timestamp_now())
    modified_date = db.Column(db.Integer, default=get_timestamp_now())

    user_id = db.Column(db.String(50), db.ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'),
                        nullable=True)
    user = db.relationship('User', viewonly=True)
    notify_type = db.Column(db.String(50), nullable=False)

    # type là loại model, id là id ban đó
    action_type = db.Column(db.String(50), nullable=True)
    action_id = db.Column(db.String(50), nullable=True)
    unread = db.Column(db.Boolean, default=True, nullable=False)

    notify_details = db.relationship('NotifyDetail', backref='notify', lazy='dynamic')

    def get_distinct_user_ids(self):
        return [
            detail.user_id
            for detail in
            self.notify_details.order_by(NotifyDetail.created_date.asc()).with_entities(NotifyDetail.user_id).distinct()
        ]

    def get_formatted_name(self, name=None):
        if name:
            if name == "ADMIN":
                return {"name": name, "other": 0, "avatar": None}
            else:
                return {"name": None, "other": 0, "avatar": None}
        first_detail = self.notify_details.order_by(asc(NotifyDetail.created_date)).first()
        total_count = len(self.get_distinct_user_ids())

        if first_detail and first_detail.user:
            return {
                'name': first_detail.user.full_name,
                'other': max(0, total_count - 1),
                'avatar': first_detail.user.avatar,
            }
        return {'name': None, 'other': 0, "avatar": None}

    @property
    def detail(self):
        if self.notify_type in [NOTIFY_TYPE["DELIVERING_ORDERS"]]:
            result = self.get_formatted_name(name="NONAME")
        elif self.notify_type in []:
            result = self.get_formatted_name(name="ADMIN")
        else:
            result = self.get_formatted_name()

        handlers = {
            "article": self._handle_article,
            "comment": self._handle_comment_related,
            "reaction": self._handle_comment_related,
            "orders": self._handle_add_order,
            "delivering_orders": self._handle_ship_order
        }

        handler = handlers.get(self.notify_type, self._handle_default)
        content, router = handler()

        result.update({'content': content, 'router': router})
        return result

    def _handle_article(self):
        """Process notifications when there is a new post"""
        article = Article.query.filter_by(id=self.action_id).first()
        if not article:
            return 'bài viết đã bị xóa', {}

        return (
            f'posted an article {article.title}',
            {"name": "PostDetail", "params": {
                "article_id": article.id,
            }}
        )

    def _handle_comment_related(self):
        """Process notifications when there are comments, reactions, or mentions"""
        if self.action_type == CONTENT_TYPE["ARTICLE"]:
            article = Article.query.filter_by(id=self.action_id).first()
            if not article:
                return 'Bài viết đã bị xóa', {}

            messages = {
                "comment": f"commented on your article {': ' + article.title}",
                "reaction": f"voted your article {': ' + article.title}",
            }

            return messages[self.notify_type], {
                "name": "PostDetail",
                "params": {
                    "article_id": article.id,
                }
            }

        comment = Comment.query.filter_by(id=self.action_id).first()
        if not comment:
            return 'bình luận đã bị xóa', {}

        messages = {
            "comment": 'replied to a comment',
            "reaction": 'voted a comment',
        }

        return messages[self.notify_type], {
            "name": "CommentDetail",
            "params": {
                "article_id": comment.article_id,
                "comment_id": comment.id,
            }
        }

    def _handle_add_order(self):

        messages = "đã đặt đơn hàng"

        return messages, {"name": "ManageOrders"}

    def _handle_ship_order(self):

        messages = f"Đơn hàng #{self.id} đã được giao cho đơn vận chuyển"

        return messages, {"name": "OrdersDelivering"}

    def _handle_default(self):
        """Default case handling"""
        return '', {}


class NotifyDetail(db.Model):
    __tablename__ = 'notify_detail'
    id = db.Column(db.String(50), primary_key=True)
    created_date = db.Column(db.Integer, default=get_timestamp_now())
    user_id = db.Column(db.String(50), db.ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'),
                        nullable=True)
    user = db.relationship('User', viewonly=True)

    # type là loại model, id là id ban đó
    action_type = db.Column(db.String(50), nullable=True)
    action_id = db.Column(db.String(50), nullable=True)

    notify_id = db.Column(db.String(50), db.ForeignKey('notify.id', ondelete='CASCADE', onupdate='CASCADE'),
                        nullable=True)


class PaymentOnline(db.Model):
    __tablename__ = 'payment_online'
    id = db.Column(db.String(50), primary_key=True)
    order_payment_id =  db.Column(db.String(100), nullable=False)
    request_payment_id = db.Column(db.String(50), nullable=False)

    session_order_id = db.Column(
        db.String(50),
        db.ForeignKey('session_order.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=True  # Cho phép NULL
    )

    result_payment = db.Column(db.JSON, nullable=True, default=None)
    status_payment = db.Column(db.Boolean, nullable=False, default=False)
    type = db.Column(db.String(20), nullable=True) # momo / zalo
    created_date = db.Column(db.Integer, default=get_timestamp_now())


class OrderReport(db.Model):
    __tablename__ = 'order_report'

    id = db.Column(db.String(50), primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'),
                        nullable=True)
    reason = db.Column(db.String(100, collation="utf8mb4_vietnamese_ci"))
    order_id = db.Column(db.String(50), db.ForeignKey('orders.id', ondelete='CASCADE', onupdate='CASCADE'),
                         nullable=True)
    order = db.relationship('Orders', viewonly=True)

    message = db.Column(db.Text(collation='utf8mb4_unicode_ci'), nullable=True)
    status = db.Column(db.String(20), default='processing')  # processing, resolved
    result = db.Column(db.Text(collation='utf8mb4_unicode_ci'), nullable=True)
    files = db.relationship(
        'Files',
        secondary='file_link',
        primaryjoin=(
            "and_(OrderReport.id == FileLink.table_id, FileLink.table_type == 'order_report')"
        ),
        secondaryjoin="FileLink.file_id == Files.id",
        lazy='dynamic',
        order_by="asc(FileLink.index)",
        viewonly=True
    )
    user = db.relationship('User', viewonly=True)

    created_date = db.Column(db.Integer, default=get_timestamp_now())
    result_date = db.Column(db.Integer, nullable=True)


class OrderItems(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.String(50), primary_key=True)
    product_id = db.Column(db.String(50), db.ForeignKey('product.id', ondelete='SET NULL', onupdate='SET NULL'),
                           nullable=True)
    order_id = db.Column(db.String(50), db.ForeignKey('orders.id', ondelete='CASCADE', onupdate='CASCADE'),
                         nullable=False)
    quantity = db.Column(db.Integer, nullable=True, default=1)
    count = db.Column(db.BigInteger, default=0)
    size_id = db.Column(db.String(50), db.ForeignKey('size.id', ondelete='SET NULL', onupdate='CASCADE'),
                        nullable=True)
    color_id = db.Column(db.String(50), db.ForeignKey('color.id', ondelete='SET NULL', onupdate='CASCADE'),
                         nullable=True)
    created_date = db.Column(db.Integer, default=get_timestamp_now())
    modified_date = db.Column(db.Integer, default=get_timestamp_now())

    product = db.relationship("Product", viewonly=True)
    color = db.relationship("Color", viewonly=True)
    size = db.relationship("Size", viewonly=True)


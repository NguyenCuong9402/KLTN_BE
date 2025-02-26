# coding: utf-8
from email.policy import default

from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, TEXT, asc, desc
from datetime import datetime

from app.enums import FILE_TYPE, DURATION_SESSION_MINUTES, TYPE_REACTION
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
    email = db.Column(db.String(100, collation="utf8mb4_vietnamese_ci"))
    phone = db.Column(db.String(50))
    password = db.Column(db.String(255))
    password_hash = db.Column(db.String(255))
    gender = db.Column(db.Boolean, default=0)
    full_name = db.Column(db.String(100, collation="utf8mb4_vietnamese_ci"))
    avatar_id = db.Column(db.String(50), db.ForeignKey('files.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    birthday = db.Column(db.DATE, nullable=True)
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
    tax_code = db.Column(db.String(100), nullable=True) # ma so thue
    join_date = db.Column(db.DateTime, nullable=True)
    finish_date = db.Column(db.DateTime, nullable=True)
    number_dependent = db.Column(INTEGER(unsigned=True), default=0) # người phụ thuộc

    avatar = db.relationship("Files", viewonly=True)

    attendances = db.relationship('Attendance', back_populates='user', cascade="all, delete-orphan")
    salaries = db.relationship('Salary', back_populates='user', cascade="all, delete-orphan")

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


class Salary(db.Model):
    __tablename__ = 'salary'

    id = db.Column(db.String(50), primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'),
                           nullable=False)
    user = db.relationship('User', viewonly=True)
    base_salary = db.Column(db.Numeric(10, 2), nullable=False)
    kpi_salary = db.Column(INTEGER(unsigned=True))
    allowance_salary = db.Column(INTEGER(unsigned=True))
    created_date = db.Column(INTEGER(unsigned=True), default=get_timestamp_now(), index=True)

class SalaryReport(db.Model):
    __tablename__ = 'salary_report'

    id = db.Column(db.String(50), primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    group_id = db.Column(ForeignKey('group.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    salary_id = db.Column(ForeignKey('salary.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=True)

    user = db.relationship('User', viewonly=True)
    group = relationship('Group', viewonly=True)
    salary = relationship('Group', viewonly=True)

    month = db.Column(db.Integer, nullable=False)  # Tháng lương
    year = db.Column(db.Integer, nullable=False)  # Năm lương
    kpi_score = db.Column(INTEGER(unsigned=True), default=0, nullable=False)
    number_dependent = db.Column(INTEGER(unsigned=True), default=0) # người phụ thuộc
    reward = db.Column(INTEGER(unsigned=True), default=0, nullable=False)

    total_salary = db.Column(db.Numeric(10, 2), nullable=False)

    created_date = db.Column(INTEGER(unsigned=True), default=get_timestamp_now(), index=True)
    modified_date = db.Column(INTEGER(unsigned=True), default=get_timestamp_now())


class DocumentStorage(db.Model):
    __tablename__ = 'document_storage'

    id = db.Column(db.String(50), primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'),
                           nullable=False)
    user = db.relationship('User', viewonly=True)

    document_name = db.Column(db.String(255, collation="utf8mb4_vietnamese_ci"), nullable=False)  # Tên tài liệu
    document_url = db.Column(db.String(500), nullable=False)  # Đường dẫn đến tài liệu
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
    created_date = db.Column(INTEGER(unsigned=True), default=get_timestamp_now(), index=True)


class FileLink(db.Model):
    __tablename__ = "file_link"

    id = db.Column(db.String(50), primary_key=True)
    file_id = db.Column(db.String(50), db.ForeignKey('files.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    # user_id =  db.Column(db.String(50), db.ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    # order_report_id = db.Column(db.String(50), db.ForeignKey('order_report.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    # product_id = db.Column(db.String(50), db.ForeignKey('product.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=True)

    table_id = db.Column(db.String(50), nullable=True)
    table_type = db.Column(db.String(50), nullable=False)

    index = db.Column(db.Integer, nullable=True, default=0)
    created_date = db.Column(INTEGER(unsigned=True), default=get_timestamp_now(), index=True)


class UserSetting(db.Model):
    __tablename__ = "user_setting"

    id = db.Column(db.String(50), primary_key=True)
    display_column = db.Column(db.Text())
    created_date = db.Column(INTEGER(unsigned=True), default=get_timestamp_now(), index=True)  # timestamp
    modified_date = db.Column(INTEGER(unsigned=True), default=get_timestamp_now())  # timestamp
    user_id = db.Column(ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'), index=True)


class Permission(db.Model):
    __tablename__ = 'permission'

    id = db.Column(db.String(50), primary_key=True)
    key = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100, collation="utf8mb4_vietnamese_ci"), nullable=False, unique=False)
    resource = db.Column(db.String(500), nullable=False, unique=False)
    is_show = db.Column(db.Boolean, default=1)
    privacy = db.Column(db.Boolean, default=0)


class Role(db.Model):
    __tablename__ = 'role'

    id = db.Column(db.String(50), primary_key=True)
    key = db.Column(db.String(100))
    name = db.Column(db.String(100, collation="utf8mb4_vietnamese_ci"), nullable=False, unique=True)
    description = db.Column(db.String(500))
    type = db.Column(db.SmallInteger, default=1)  # tổng của 4 loại quyền sau 1: Xem, 2: Thêm, 4: Sửa, 8: Xóa
    created_date = db.Column(INTEGER(unsigned=True), default=get_timestamp_now())
    modified_date = db.Column(INTEGER(unsigned=True), default=get_timestamp_now())
    last_modified_user = db.Column(ForeignKey('user.id', ondelete='SET NULL', onupdate='CASCADE'))
    created_user = db.Column(ForeignKey('user.id', ondelete='SET NULL', onupdate='CASCADE'))

    modified_user_data = relationship('User', foreign_keys="Role.last_modified_user")
    created_user_data = relationship('User', foreign_keys="Role.created_user")
    group_role = relationship('GroupRole', primaryjoin='GroupRole.role_id == Role.id', viewonly=True)
    role_permission = relationship('RolePermission', primaryjoin='RolePermission.role_id == Role.id', viewonly=True)

    @classmethod
    def get_by_id(cls, _id):
        return cls.query.get(_id)

    @property
    def number_of_group_role(self):
        return len(self.group_role)


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

    @property
    def created_user(self):
        if self.created_user_fk:
            return User.query.filter_by(id=self.created_user_fk).first()
        return None


class Message(db.Model):
    __tablename__ = 'message'

    id = db.Column(db.String(50), primary_key=True)
    description = db.Column(db.String(255))
    show = db.Column(db.Boolean, default=0)
    duration = db.Column(db.Integer, default=5)
    status = db.Column(db.String(20), default='success')
    message = db.Column(db.String(500), nullable=False)
    dynamic = db.Column(db.Boolean, default=0)
    object = db.Column(db.String(255))


class EmailTemplate(db.Model):
    __tablename__ = 'email_template'

    id = db.Column(db.String(50), primary_key=True)
    body = db.Column(TEXT())
    template_code = db.Column(db.String(200))
    object = db.Column(db.JSON)


class Mail(db.Model):
    __tablename__ = 'mail'
    id = db.Column(db.String(50), primary_key=True)
    body = db.Column(TEXT())
    email = db.Column(db.String(100, collation="utf8mb4_vietnamese_ci"))
    created_date = db.Column(INTEGER(unsigned=True), default=get_timestamp_now(), index=True)


class VerityCode(db.Model):
    __tablename__ = 'verity_code'

    id = db.Column(db.String(50), primary_key=True)
    code = db.Column(db.String(20))
    user_id = db.Column(db.String(50), db.ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'),
                        nullable=True)
    mail_id = db.Column(db.String(50), db.ForeignKey('mail.id', ondelete='CASCADE', onupdate='CASCADE'),
                        nullable=True)
    type = db.Column(db.Integer, default=1)  # 1: đăng ký
    # thêm thời gian giới hạn

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
    payment_status = db.Column(db.Boolean, nullable=False, default=False)

    payment_online_id = db.Column(db.String(50), db.ForeignKey('payment_online.id', ondelete='SET NULL', onupdate='SET NULL'))

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


class PaymentOnline(db.Model):
    __tablename__ = 'payment_online'
    id = db.Column(db.String(50), primary_key=True)
    order_payment_id =  db.Column(db.String(100), nullable=False)
    request_payment_id = db.Column(db.String(50), nullable=False)
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


class Reviews(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.String(50), primary_key=True)
    product_id = db.Column(db.String(50), db.ForeignKey('product.id', ondelete='CASCADE', onupdate='CASCADE'),
                           nullable=True)
    user_id = db.Column(db.String(50), db.ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'),
                        nullable=True)
    body = db.Column(db.Text(collation='utf8mb4_unicode_ci'), nullable=True)
    body_type = db.Column(db.String(20), nullable=True)
    created_date = db.Column(db.Integer, default=get_timestamp_now())
    modified_date = db.Column(db.Integer, default=get_timestamp_now())
    review_id = db.Column(db.String(50), db.ForeignKey('reviews.id', ondelete='CASCADE',
                                                       onupdate='CASCADE'), nullable=True)

import json
import uuid
from datetime import timedelta
from flask import Blueprint, request
from flask_jwt_extended import (get_jwt_identity, jwt_required)
from marshmallow import ValidationError
from sqlalchemy import desc, asc
from sqlalchemy_pagination import paginate

from app.enums import  GROUP_KEY_PARAM
from app.api.helper import get_permissions, CONFIG, send_email_template, get_roles_key, Token, convert_to_datetime, \
    get_user_id_request
from app.api.helper import send_error, send_result
from app.extensions import jwt, db
from app.models import User, Address, Article, Community
from app.utils import trim_dict, get_timestamp_now, data_preprocessing, generate_random_number_string, \
    body_mail, escape_wildcard
from app.extensions import mail

from app.validator import UserSchema, UserValidation, QueryParamsArticleSchema, ArticleSchema

api = Blueprint('profile', __name__)


@api.route('', methods=['GET'])
def profile():
    user_id = get_user_id_request()
    profile_id = request.args.get("profile_id", None)

    if not profile_id and not user_id:
        return send_error(message='Bạn chưa đăng nhập')

    if profile_id:
        user = User.query.filter_by(id=profile_id).first()
    else:
        user = User.query.filter_by(id=user_id).first()


    data = UserSchema().dump(user)

    data['param_router'] = GROUP_KEY_PARAM.get(user.group.key, '/')

    return send_result(data=data)

@api.route('', methods=['PUT'])
@jwt_required
def update_profile():
    try:
        user_id = get_jwt_identity()
        json_req = request.get_json()
        json_body = trim_dict(json_req)
        validator_input = UserValidation()
        is_not_validate = validator_input.validate(json_body)
        if is_not_validate:
            return send_error(data=is_not_validate, message='Validate Error')

        user = User.query.filter_by(id=user_id).first()
        if user is None:
            return send_error(message="Người dùng không hợp lệ")

        address = json_body.pop('address')
        if json_body.get('birthday', None):
            json_body['birthday'] = convert_to_datetime(json_body.get('birthday'))

        for key, value in address.items():
            if value is None or value.strip() =='':
                return send_error(message='Vui lòng chọn địa chỉ')

        address = Address.query.filter_by(province=address.get('province'), district=address.get('district'),
                                          ward=address.get('ward')).first()
        if address is None:
            return send_error(message="Địa chỉ không hợp lệ.")
        user.address_id = address.id

        for key, value in json_body.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)

        db.session.flush()
        db.session.commit()
        data =  UserSchema().dump(user)
        data.setdefault('param_router', GROUP_KEY_PARAM.get(user.group.key, '/'))

        return send_result(data=data, message='Thành công')
    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex), code=442)


@api.route('/article', methods=['GET'])
def get_articles():
    try:
        try:
            params = request.args.to_dict(flat=True)
            params = QueryParamsArticleSchema().load(params) if params else dict()
        except ValidationError as err:
            return send_error(message='INVALID_PARAMETERS_ERROR', data=err.messages)
        page = params.get('page', 1)
        page_size = params.get('page_size', 10)
        order_by = params.get('order_by', 'created_date')
        sort = params.get('sort', 'desc')
        text_search = params.get('text_search', '')
        community_id = params.get('community_id')
        timestamp = params.get('timestamp')
        profile_id = params.get('profile_id')

        query = Article.query.filter()
        user_id = get_user_id_request()

        if not profile_id and not user_id:
            return send_error(message='Bạn chưa đăng nhập')

        if profile_id:
            user_profile = User.query.filter_by(id=profile_id).first()
            if user_profile is None:
                return send_error(message='Hồ sơ người dùng không tồn tại')

            query = query.filter(Article.user_id==profile_id)
        else:
            query = query.filter(Article.user_id==user_id)



        if community_id:
            check_community = Community.query.filter_by(id=community_id).first()
            if check_community is None:
                return send_error(message='Nhóm không tồn tại')
            query = query.filter(Article.community_id == community_id)
        if timestamp:
            query = query.filter(Article.modified_date < timestamp)

        if text_search:
            text_search = text_search.strip()
            text_search = text_search.lower()
            text_search = escape_wildcard(text_search)
            text_search = "%{}%".format(text_search)
            query = query.filter(Article.title.ilike(text_search))

        column_sorted = getattr(Article, order_by)

        query = query.order_by(desc(column_sorted)) if sort == "desc" else query.order_by(asc(column_sorted))

        paginator = paginate(query, page, page_size)



        products = ArticleSchema(many=True, context={"user_id": user_id}).dump(paginator.items)

        response_data = dict(
            items=products,
            total_pages=paginator.pages if paginator.pages > 0 else 1,
            total=paginator.total,
            has_previous=paginator.has_previous,  # Có trang trước không
            has_next=paginator.has_next  # Có trang sau không
        )


        return send_result(data=response_data,  message='Thành công')

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex), code=442)



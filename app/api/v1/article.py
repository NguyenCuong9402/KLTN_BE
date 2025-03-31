import json
from shortuuid import uuid
from flask import Blueprint, request
from marshmallow import ValidationError
from sqlalchemy import desc, asc
from sqlalchemy.sql.visitors import replacement_traverse
from sqlalchemy_pagination import paginate

from app.enums import LAYER_COMMENT
from app.extensions import logger, db
from flask_jwt_extended import get_jwt_identity, jwt_required, verify_jwt_in_request_optional
from app.api.helper import send_result, send_error, get_user_id_request
from app.models import User, Article, Community, Product, ArticleTagProduct, Comment
from app.utils import trim_dict, escape_wildcard, get_timestamp_now
from app.validator import ProductValidation, ArticleSchema, QueryParamsAllSchema, ArticleValidate, \
    QueryParamsArticleSchema, CommentParamsValidation, CommentSchema

api = Blueprint('article', __name__)


@api.route('', methods=['POST'])
@jwt_required
def create_article():
    try:
        user_id = get_jwt_identity()
        json_req = request.get_json()
        json_body = trim_dict(json_req)
        validator_input = ArticleValidate()
        is_not_validate = validator_input.validate(json_body)
        if is_not_validate:
            return send_error(data=is_not_validate, message='Validate Error')
        community_id = json_body.get('community_id')
        community = Community.query.filter_by(id=community_id).first()
        if community is None:
            return send_error(message='Nhóm không tồn tại.')
        tags = json_body.pop('tags', [])
        if tags and Product.query.filter(Product.id.in_(tags)).count() < len(tags):
            return send_error(message='Có tag không tồn tại.')
        artice = Article(
            id=str(uuid()),
            user_id=user_id,
            **json_body
        )
        db.session.add(artice)
        tag_product = [ArticleTagProduct(id=str(uuid()), article_id=artice.id, product_id=product_id, index=index)
                       for  index, product_id in enumerate(tags)]
        db.session.bulk_save_objects(tag_product)
        db.session.flush()
        db.session.commit()
        return send_result(message='Thành công', data={'article_id': artice.id})

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex), code=442)


@api.route("/<article_id>", methods=["DELETE"])
@jwt_required
def remove_article(article_id):
    try:
        user_id = get_jwt_identity()
        user = User.query.filter(User.id == user_id).first()
        if user is None:
            return send_error(message='User not found', code=404)
        artice = Article.query.filter(Article.id == article_id, user.id == user.id)
        if artice.first() is None:
            return send_error(message='Article not found', code=404)
        artice.delete()
        db.session.flush()
        db.session.commit()
        return send_result(message="Xóa bài viết thành công")
    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex))


@api.route('', methods=['GET'])
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

        query = Article.query.filter()
        user_id = get_user_id_request()
        if community_id:
            check_community = Community.query.filter_by(id=community_id).first()
            if check_community is None:
                return send_error(message='Community not found', code=404)
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


        return send_result(data= response_data,  message='Thành công')

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex), code=442)


@api.route("/<article_id>", methods=["GET"])
def get_article(article_id):
    try:
        user_id = get_user_id_request()
        query = Article.query.filter(Article.id == article_id).first()
        if query is None:
            return send_error(message='Article not found', code=404)
        data = ArticleSchema(context={"user_id": user_id}).dump(query)
        return send_result(data=data, message="success")
    except Exception as ex:
        return send_error(message=str(ex))



@api.route('/<article_id>/comment', methods=['GET'])
def get_comment_article(article_id):
    try:
        try:
            params = request.args.to_dict(flat=True)
            params = CommentParamsValidation().load(params) if params else dict()
        except ValidationError as err:
            return send_error(message='INVALID_PARAMETERS_ERROR', data=err.messages)
        page = params.get('page', 1)
        page_size = params.get('page_size', 10)
        order_by = params.get('order_by', 'created_date')
        sort = params.get('sort', 'desc')

        query = Comment.query.filter(
            Comment.article_id == article_id,
            Comment.ancestry_id.is_(None)
        )

        user_id = get_user_id_request()

        query = query.order_by(desc(Comment.created_date)) if sort == "desc" else query.order_by(asc(Comment.created_date))

        paginator = paginate(query, page, page_size)
        comments = CommentSchema(many=True, context={"user_id": user_id, "order_by": order_by,
                                                     "sort": sort, "depth": LAYER_COMMENT}).dump(paginator.items)

        response_data = dict(
            items=comments,
            total_pages=paginator.pages if paginator.pages > 0 else 1,
            total=paginator.total,
            has_previous=paginator.has_previous,
            has_next=paginator.has_next
        )


        return send_result(data= response_data,  message='Thành công')

    except Exception as ex:
        db.session.rollback()
        return send_error(message=str(ex), code=442)


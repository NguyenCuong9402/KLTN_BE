# -*- coding: utf-8 -*-
from time import strftime

from flask import Flask, request
from flask_cors import CORS

from app.api.helper import CONFIG, send_result
from app.extensions import logger, jwt, db, red, mail, migrate, scheduler
from .api import v1 as api_v1
from .api.helper import send_error
from .enums import TIME_FORMAT_LOG
from .scheduler_task import backup_data


def create_app(config_object=CONFIG):
    """
    Init App
    :param config_object:
    :return:
    """
    app = Flask(__name__, static_url_path="/files", static_folder="./files")
    app.config.from_object(config_object)
    register_extensions(app)
    register_blueprints(app)
    register_monitor(app)
    CORS(app, expose_headers=["Content-Disposition"])
    if config_object.ENV == 'prd':
        # Task Scheduler backup data runs every 2 week at 03:00:00pm
        scheduler.add_job(backup_data, trigger='cron', hour='15', minute='00', second='00')
    return app


def register_extensions(app):
    """
    Init extension
    :param app:
    :return:
    """

    db.app = app
    db.init_app(app)  # SQLAlchemy
    jwt.init_app(app)
    red.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    @app.after_request
    def after_request(response):
        """

        :param response:
        :return:
        """
        # This IF avoids the duplication of registry in the log,
        # status code greater than 400 is already logged in @app.errorhandler.
        if 200 <= response.status_code < 400:
            ts = strftime(TIME_FORMAT_LOG)
            logger.info('%s %s %s %s %s %s',
                        ts,
                        request.remote_addr,
                        request.method,
                        request.scheme,
                        request.full_path,
                        response.status)
        return response

    @app.errorhandler(Exception)
    def exceptions(e):
        """
        Handling exceptions
        :param e:
        :return:
        """
        ts = strftime(TIME_FORMAT_LOG)
        error = '{} {} {} {} {} {}'.format(ts, request.remote_addr, request.method, request.scheme, request.full_path,
                                           str(e))
        code = 500
        if hasattr(e, 'code'):
            code = e.code
        if code == 500:
            logger.error(error)
        else:
            logger.info(error)

        return send_error(message=str(e), code=code)


def register_monitor(app):
    def has_no_empty_params(rule):
        defaults = rule.defaults if rule.defaults is not None else ()
        arguments = rule.arguments if rule.arguments is not None else ()
        return len(defaults) >= len(arguments)

    @app.route("/api/v1/helper/site-map", methods=['GET'])
    def site_map():
        links = []
        for rule in app.url_map.iter_rules():
            # Filter out rules we can't navigate to in a browser
            # and rules that require parameters
            # if has_no_empty_params(rule):

            # url = url_for(rule.endpoint, **(rule.defaults or {}))
            request_method = ""
            if "GET" in rule.methods:
                request_method = "get"
            if "PUT" in rule.methods:
                request_method = "put"
            if "POST" in rule.methods:
                request_method = "post"
            if "DELETE" in rule.methods:
                request_method = "delete"
            permission_route = "{0}@{1}".format(request_method.lower(), rule)
            links.append(permission_route)
        return send_result(data=sorted(links, key=lambda resource: str(resource).split('@')[-1]))


def register_blueprints(app):
    """
    Init blueprint for api url
    :param app:
    :return:
    """
    # Management
    app.register_blueprint(api_v1.manage.product.api, url_prefix='/api/v1/manage/product')
    app.register_blueprint(api_v1.manage.order.api, url_prefix='/api/v1/manage/order')
    app.register_blueprint(api_v1.manage.type_product.api, url_prefix='/api/v1/manage/type_product')
    app.register_blueprint(api_v1.manage.user.api, url_prefix='/api/v1/manage/user')




    # User
    app.register_blueprint(api_v1.auth.api, url_prefix='/api/v1/auth')
    app.register_blueprint(api_v1.profile.api, url_prefix='/api/v1/profile')
    app.register_blueprint(api_v1.file.api, url_prefix='/api/v1/file')
    app.register_blueprint(api_v1.product.api, url_prefix='/api/v1/product')
    app.register_blueprint(api_v1.cart.api, url_prefix='/api/v1/cart')
    app.register_blueprint(api_v1.address.api, url_prefix='/api/v1/address')
    app.register_blueprint(api_v1.session_order.api, url_prefix='/api/v1/session_order')
    app.register_blueprint(api_v1.order.api, url_prefix='/api/v1/order')
    app.register_blueprint(api_v1.shipper.api, url_prefix='/api/v1/shipper')
    app.register_blueprint(api_v1.order_report.api, url_prefix='/api/v1/order_report')
    app.register_blueprint(api_v1.community.api, url_prefix='/api/v1/community')
    app.register_blueprint(api_v1.article.api, url_prefix='/api/v1/article')
    app.register_blueprint(api_v1.reaction.api, url_prefix='/api/v1/reaction')
    app.register_blueprint(api_v1.comment.api, url_prefix='/api/v1/comment')
    app.register_blueprint(api_v1.type_product.api, url_prefix='/api/v1/type_product')
    app.register_blueprint(api_v1.payment_online.api, url_prefix='/api/v1/payment_online')


















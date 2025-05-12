# -*- coding: utf-8 -*-
from flask import Flask
from flask_cors import CORS

from app.api.helper import CONFIG, send_result
from app.extensions import jwt, db, red, mail, migrate, scheduler
from .api import v1 as api_v1
from .scheduler_task import backup_data, run_consumers_in_thread, resolved_orders, attendance
import requests


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
    from app import signal
    if config_object.ENABLE_RABBITMQ_CONSUMER:
        run_consumers_in_thread(app)

    if config_object.ENV == 'prd':
        scheduler.add_job(
            resolved_orders,
            trigger='cron',
            hour=0,
            minute=0,
            id='resolved_orders',
            replace_existing=True,
            misfire_grace_time=60  # cho phép trễ tối đa 60s
        )

        scheduler.add_job(
            attendance,
            trigger='cron',
            day=1,
            hour=2,
            minute=0,
            id='attendance',
            replace_existing=True,
            misfire_grace_time=60
        )

        scheduler.add_job(
            backup_data,
            trigger='interval',
            minutes=2,
            id='backup_data',
            replace_existing=True,
            misfire_grace_time=30
        )



    elif config_object.ENV == 'stg':
        scheduler.add_job(resolved_orders, trigger='interval', minutes=1)
        scheduler.add_job(attendance, trigger='interval', minutes=2)
        scheduler.add_job(backup_data, trigger='interval', minutes=1)


    # Run webhook bot tele
    try:
        delete_webhook_url = f"https://api.telegram.org/bot{config_object.TOKEN_BOT_TELE}/deleteWebhook"
        requests.get(delete_webhook_url)

        # Step 2: Set a new webhook
        set_webhook_url = f"https://api.telegram.org/bot{config_object.TOKEN_BOT_TELE}/setWebhook?url={config_object.BASE_URL_WEBSITE}/api/v1/bot_tele"
        requests.get(set_webhook_url)
    except:
        pass
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

    # @app.after_request
    # def after_request(response):
    #     """
    #
    #     :param response:
    #     :return:
    #     """
    #     # This IF avoids the duplication of registry in the log,
    #     # status code greater than 400 is already logged in @app.errorhandler.
    #     if 200 <= response.status_code < 400:
    #         ts = strftime(TIME_FORMAT_LOG)
    #         logger.info('%s %s %s %s %s %s',
    #                     ts,
    #                     request.remote_addr,
    #                     request.method,
    #                     request.scheme,
    #                     request.full_path,
    #                     response.status)
    #     return response

    # @app.errorhandler(Exception)
    # def exceptions(e):
    #     """
    #     Handling exceptions
    #     :param e:
    #     :return:
    #     """
    #     ts = strftime(TIME_FORMAT_LOG)
    #     error = '{} {} {} {} {} {}'.format(ts, request.remote_addr, request.method, request.scheme, request.full_path,
    #                                        str(e))
    #     code = 500
    #     if hasattr(e, 'code'):
    #         code = e.code
    #     if code == 500:
    #         logger.error(error)
    #     else:
    #         logger.info(error)
    #
    #     return send_error(message=str(e), code=code)


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
    app.register_blueprint(api_v1.manage.shipper.api, url_prefix='/api/v1/manage/shipper')
    app.register_blueprint(api_v1.manage.region.api, url_prefix='/api/v1/manage/region')
    app.register_blueprint(api_v1.manage.group.api, url_prefix='/api/v1/manage/group')
    app.register_blueprint(api_v1.manage.statistic.api, url_prefix='/api/v1/manage/statistic')
    app.register_blueprint(api_v1.manage.report.api, url_prefix='/api/v1/manage/report')
    app.register_blueprint(api_v1.manage.document.api, url_prefix='/api/v1/manage/document')
    app.register_blueprint(api_v1.manage.attendance.api, url_prefix='/api/v1/manage/attendance')


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
    app.register_blueprint(api_v1.notify.api, url_prefix='/api/v1/notify')
    app.register_blueprint(api_v1.bot_tele.api, url_prefix='/api/v1/bot_tele')


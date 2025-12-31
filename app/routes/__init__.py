"""
路由模块
"""
from flask import Blueprint
from .auth import auth_bp
from .admin import admin_bp
from .iptv import iptv_bp
from .schedule import schedule_bp
from .account import account_bp
from .logs import logs_bp
from .channel_template import channel_template_bp


def register_blueprints(app):
    """
    注册所有蓝图
    
    Args:
        app: Flask 应用实例
    """
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(iptv_bp)
    app.register_blueprint(schedule_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(channel_template_bp)


__all__ = [
    'auth_bp',
    'admin_bp',
    'iptv_bp',
    'schedule_bp',
    'account_bp',
    'logs_bp',
    'channel_template_bp',
    'register_blueprints',
]

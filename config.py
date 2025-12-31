"""
配置管理 - 环境变量和常量配置
"""
import os
from datetime import timedelta

# 基础路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# 确保目录存在
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)


class Config:
    """基础配置"""
    # Flask 配置
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-2025')
    
    # 数据库配置
    DATABASE_PATH = os.path.join(DATA_DIR, 'iptv.db')
    print(f"DATA_DIR: {DATA_DIR}")  # 调试输出
    
    # JWT 配置
    JWT_SECRET = os.environ.get('JWT_SECRET', 'iptv-system-secret-key-2025')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_DAYS = 7
    
    # 应用配置
    APP_NAME = 'IPTV 后台管理系统'
    APP_VERSION = '3.1.0'
    
    # API 配置
    API_BASE_URL = '/api'
    API_TIMEOUT = 30
    
    # 安全配置
    PASSWORD_MIN_LENGTH = 6
    PASSWORD_MAX_LENGTH = 128
    USERNAME_MIN_LENGTH = 3
    USERNAME_MAX_LENGTH = 32
    
    # 默认管理员配置
    DEFAULT_ADMIN_USERNAME = 'admin'
    DEFAULT_ADMIN_PASSWORD = 'adminadmin'


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """测试环境配置"""
    DEBUG = True
    TESTING = True
    DATABASE_PATH = os.path.join(DATA_DIR, 'test_iptv.db')


# 配置选择
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """获取配置对象"""
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])

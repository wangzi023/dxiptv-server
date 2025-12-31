"""
认证工具 - JWT 令牌生成和验证
"""
import hashlib
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from config import get_config


config = get_config()


def hash_password(password):
    """
    密码哈希
    
    Args:
        password (str): 明文密码
        
    Returns:
        str: SHA256 哈希值
    """
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password, password_hash):
    """
    验证密码
    
    Args:
        password (str): 明文密码
        password_hash (str): 密码哈希值
        
    Returns:
        bool: 是否匹配
    """
    return hash_password(password) == password_hash


def generate_token(user_id, username, expires_in=None):
    """
    生成 JWT 令牌
    
    Args:
        user_id (int): 用户 ID
        username (str): 用户名
        expires_in (int): 过期时间（天数），默认 7 天
        
    Returns:
        str: JWT 令牌
    """
    if expires_in is None:
        expires_in = config.JWT_EXPIRATION_DAYS
    
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.utcnow() + timedelta(days=expires_in),
        'iat': datetime.utcnow()
    }
    
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


def verify_token(token):
    """
    验证 JWT 令牌
    
    Args:
        token (str): JWT 令牌
        
    Returns:
        dict: 令牌载荷，如果无效则返回 None
    """
    from app.utils import get_logger
    logger = get_logger('auth')
    
    try:
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
        logger.info(f'Token解码成功，用户: {payload.get("username")}')
        return payload
    except jwt.ExpiredSignatureError as e:
        logger.warning(f'Token已过期: {str(e)}')
        return None
    except jwt.InvalidTokenError as e:
        logger.error(f'Token无效: {str(e)}')
        return None


def token_required(f):
    """
    需要令牌的装饰器
    
    使用方法:
        @app.route('/api/protected')
        @token_required
        def protected_route():
            user_id = request.user['user_id']
            return jsonify({'user_id': user_id})
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        from app.utils import get_logger
        logger = get_logger('auth')
        
        token = request.headers.get('Authorization')
        
        logger.info(f'收到请求 {request.path}, Authorization头: {token[:50] if token else None}...')
        
        if not token:
            logger.warning('未提供Authorization头')
            return jsonify({'error': '未授权，请先登录'}), 401
        
        # 移除 Bearer 前缀
        if token.startswith('Bearer '):
            token = token[7:]
        elif token.startswith('bearer '):
            token = token[7:]
        
        logger.info(f'提取的token (前20字符): {token[:20]}...')
        
        payload = verify_token(token)
        if not payload:
            logger.warning(f'Token验证失败: {token[:20]}...')
            return jsonify({'error': '令牌无效或已过期'}), 401
        
        logger.info(f'Token验证成功，用户: {payload.get("username")}')
        
        # 将用户信息存储在 request 对象中
        request.user = payload
        return f(*args, **kwargs)
    
    return decorated

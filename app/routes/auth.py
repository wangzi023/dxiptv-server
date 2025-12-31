"""
认证路由
"""
from flask import Blueprint, request, jsonify
from app.services import UserService, LogService
from app.utils import token_required

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/check-admin', methods=['GET'])
def check_admin():
    """检查是否存在管理员"""
    try:
        from app.utils import execute_query
        
        result = execute_query(
            'SELECT COUNT(*) as count FROM users',
            fetch_one=True
        )
        
        return jsonify({'has_admin': result['count'] > 0})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({'error': '用户名和密码为必填项'}), 400
        
        # 验证凭证
        user_info = UserService.authenticate(username, password)
        
        if not user_info:
            LogService.log_auth('login_fail', f'用户 {username} 登录失败', None, username)
            return jsonify({'error': '用户名或密码错误'}), 401
        
        LogService.log_auth('login', f'用户 {username} 登录成功', user_info['id'], username)

        return jsonify({
            'message': '登录成功',
            'token': user_info['token'],
            'is_first_login': user_info['is_first_login'],
            'user': {
                'id': user_info['id'],
                'username': user_info['username'],
                'role': user_info['role'],
                'is_default': user_info['is_default']
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/verify', methods=['GET'])
@token_required
def verify():
    """验证令牌"""
    try:
        user_info = UserService.get_user_by_id(request.user['user_id'])
        
        if not user_info:
            return jsonify({'error': '用户不存在'}), 404
        
        return jsonify({
            'message': '令牌有效',
            'user': {
                'id': user_info['id'],
                'username': user_info['username'],
                'role': user_info['role'],
                'is_default': user_info['is_default']
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/change-password', methods=['POST'])
@token_required
def change_password():
    """修改密码"""
    try:
        data = request.json
        old_password = data.get('old_password', '').strip()
        new_password = data.get('new_password', '').strip()
        
        if not old_password or not new_password:
            return jsonify({'error': '旧密码和新密码为必填项'}), 400
        
        user_id = request.user['user_id']
        
        success, message = UserService.change_password(user_id, old_password, new_password)
        
        if not success:
            return jsonify({'error': message}), 400
        
        return jsonify({'message': message})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout():
    """用户登出，仅用于记录日志"""
    try:
        user = getattr(request, 'user', None)
        LogService.log_auth('logout', f"用户 {user.get('username')} 登出" if user else '用户登出',
                            user.get('user_id') if user else None,
                            user.get('username') if user else None)
        return jsonify({'message': '已登出'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

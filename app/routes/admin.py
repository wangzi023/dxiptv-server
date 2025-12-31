"""
管理员管理路由
"""
from flask import Blueprint, request, jsonify
from app.services import AdminService
from app.services.log_service import LogService
from app.utils import token_required

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admins')


@admin_bp.route('', methods=['GET'])
@token_required
def get_admins():
    """获取所有管理员列表"""
    try:
        admins = AdminService.get_all_admins()

        actor = getattr(request, 'user', {})
        LogService.log_operation(
            action='admin_list',
            message='查询管理员列表',
            user_id=actor.get('user_id'),
            username=actor.get('username'),
            status='success'
        )

        return jsonify({
            'data': admins
        })
    except Exception as e:
        actor = getattr(request, 'user', {})
        LogService.log_operation(
            action='admin_list',
            message=f'查询管理员列表失败: {e}',
            user_id=actor.get('user_id'),
            username=actor.get('username'),
            status='failed'
        )
        return jsonify({'error': str(e)}), 500


@admin_bp.route('', methods=['POST'])
@token_required
def create_admin():
    """创建新管理员（仅默认管理员可用）"""
    try:
        actor = getattr(request, 'user', {})

        # 检查是否为默认管理员
        if not AdminService.is_default_admin(request.user['user_id']):
            LogService.log_operation(
                action='admin_create',
                message='非默认管理员尝试创建管理员',
                user_id=actor.get('user_id'),
                username=actor.get('username'),
                status='failed'
            )
            return jsonify({'error': '只有默认管理员可以创建新管理员'}), 403
        
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        # 创建管理员
        success, result = AdminService.create_admin(username, password)

        if not success:
            LogService.log_operation(
                action='admin_create',
                message=f'创建管理员失败: {result}',
                user_id=actor.get('user_id'),
                username=actor.get('username'),
                status='failed'
            )
            return jsonify({'error': result}), 400

        LogService.log_operation(
            action='admin_create',
            message=f'创建管理员成功 id={result}',
            user_id=actor.get('user_id'),
            username=actor.get('username'),
            status='success'
        )

        return jsonify({
            'message': '管理员创建成功',
            'admin_id': result
        }), 201
    except Exception as e:
        actor = getattr(request, 'user', {})
        LogService.log_operation(
            action='admin_create',
            message=f'创建管理员异常: {e}',
            user_id=actor.get('user_id'),
            username=actor.get('username'),
            status='failed'
        )
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/<int:admin_id>', methods=['PUT'])
@token_required
def update_admin(admin_id):
    """修改管理员信息"""
    try:
        actor = getattr(request, 'user', {})
        current_user_id = request.user['user_id']
        data = request.json or {}
        
        # 构建更新参数
        update_params = {}
        
        if 'new_password' in data:
            update_params['new_password'] = data.get('new_password', '').strip()
        
        if 'old_password' in data:
            update_params['old_password'] = data.get('old_password', '').strip()
        
        if 'is_active' in data:
            update_params['is_active'] = data.get('is_active')
        
        # 更新管理员
        success, message = AdminService.update_admin(
            admin_id,
            current_user_id,
            **update_params
        )

        if not success:
            LogService.log_operation(
                action='admin_update',
                message=f'更新管理员 {admin_id} 失败: {message}',
                user_id=actor.get('user_id'),
                username=actor.get('username'),
                status='failed'
            )
            return jsonify({'error': message}), 400

        LogService.log_operation(
            action='admin_update',
            message=f'更新管理员 {admin_id} 成功',
            user_id=actor.get('user_id'),
            username=actor.get('username'),
            status='success'
        )

        return jsonify({'message': message})
    except Exception as e:
        actor = getattr(request, 'user', {})
        LogService.log_operation(
            action='admin_update',
            message=f'更新管理员 {admin_id} 异常: {e}',
            user_id=actor.get('user_id'),
            username=actor.get('username'),
            status='failed'
        )
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/<int:admin_id>', methods=['DELETE'])
@token_required
def delete_admin(admin_id):
    """删除管理员（仅默认管理员可用）"""
    try:
        actor = getattr(request, 'user', {})

        if not AdminService.is_default_admin(request.user['user_id']):
            LogService.log_operation(
                action='admin_delete',
                message=f'非默认管理员尝试删除管理员 {admin_id}',
                user_id=actor.get('user_id'),
                username=actor.get('username'),
                status='failed'
            )
            return jsonify({'error': '只有默认管理员可以删除管理员'}), 403

        success, message = AdminService.delete_admin(admin_id)

        if not success:
            LogService.log_operation(
                action='admin_delete',
                message=f'删除管理员 {admin_id} 失败: {message}',
                user_id=actor.get('user_id'),
                username=actor.get('username'),
                status='failed'
            )
            return jsonify({'error': message}), 400

        LogService.log_operation(
            action='admin_delete',
            message=f'删除管理员 {admin_id} 成功',
            user_id=actor.get('user_id'),
            username=actor.get('username'),
            status='success'
        )

        return jsonify({'message': message})
    except Exception as e:
        actor = getattr(request, 'user', {})
        LogService.log_operation(
            action='admin_delete',
            message=f'删除管理员 {admin_id} 异常: {e}',
            user_id=actor.get('user_id'),
            username=actor.get('username'),
            status='failed'
        )
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/<int:admin_id>/toggle', methods=['PUT'])
@token_required
def toggle_admin_status(admin_id):
    """启用/禁用管理员（仅默认管理员可用）"""
    try:
        actor = getattr(request, 'user', {})
        current_user_id = request.user['user_id']
        
        # 检查是否为默认管理员
        if not AdminService.is_default_admin(current_user_id):
            LogService.log_operation(
                action='admin_toggle',
                message=f'非默认管理员尝试切换管理员 {admin_id} 状态',
                user_id=actor.get('user_id'),
                username=actor.get('username'),
                status='failed'
            )
            return jsonify({'error': '只有默认管理员可以启用/禁用管理员'}), 403

        data = request.json or {}
        is_active = data.get('is_active', True)

        # 更新管理员状态
        success, message = AdminService.update_admin(
            admin_id,
            current_user_id,
            is_active=is_active
        )

        if not success:
            LogService.log_operation(
                action='admin_toggle',
                message=f'切换管理员 {admin_id} 状态失败: {message}',
                user_id=actor.get('user_id'),
                username=actor.get('username'),
                status='failed'
            )
            return jsonify({'error': message}), 400

        LogService.log_operation(
            action='admin_toggle',
            message=f'切换管理员 {admin_id} 状态为 {is_active}',
            user_id=actor.get('user_id'),
            username=actor.get('username'),
            status='success'
        )

        return jsonify({'message': message})
    except Exception as e:
        actor = getattr(request, 'user', {})
        LogService.log_operation(
            action='admin_toggle',
            message=f'切换管理员 {admin_id} 状态异常: {e}',
            user_id=actor.get('user_id'),
            username=actor.get('username'),
            status='failed'
        )
        return jsonify({'error': str(e)}), 500

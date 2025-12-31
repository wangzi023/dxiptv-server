"""
账户管理 API 路由
提供 /api/accounts 端点作为快捷访问方式
"""

from flask import Blueprint, request, jsonify
from app.utils.auth import token_required
from app.utils import execute_query, execute_update, get_logger
from app.services import LogService

logger = get_logger('account_routes')

account_bp = Blueprint('account', __name__, url_prefix='/api')


@account_bp.route('/accounts', methods=['GET'])
@token_required
def get_accounts():
    """
    获取账户列表
    
    Response:
    {
        "data": [
            {
                "id": 1,
                "username": "user@iptv.gd",
                "mac": "00:11:22:33:44:55",
                "status": 0
            }
        ]
    }
    """
    try:
        sql = """
            SELECT id, username, mac, imei, address, remark, status, created_at, updated_at
            FROM accounts
            ORDER BY created_at DESC
        """
        accounts = execute_query(sql, ())
        
        return jsonify({
            'data': accounts
        }), 200
        
    except Exception as e:
        logger.error(f'获取账户列表异常: {e}')
        return jsonify({
            'error': f'系统异常: {str(e)}'
        }), 500


@account_bp.route('/accounts', methods=['POST'])
@token_required
def create_account():
    """
    创建新账户
    
    Request Body:
    {
        "username": "user@iptv.gd",
        "password": "password",
        "mac": "00:11:22:33:44:55",
        "imei": "123456789012345",
        "address": "广东"
    }
    """
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        mac = data.get('mac', '').strip()
        imei = data.get('imei', '').strip()
        address = data.get('address', '').strip()
        remark = data.get('remark', '').strip()
        
        if not username or not password:
            return jsonify({'error': '用户名和密码不能为空'}), 400
        
        # 检查用户名是否已存在
        check_sql = "SELECT id FROM accounts WHERE username = ?"
        existing = execute_query(check_sql, (username,))
        if existing:
            return jsonify({'error': '用户名已存在'}), 400
        
        # 创建账户
        sql = """
            INSERT INTO accounts (username, password, mac, imei, address, remark, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 0, datetime('now'), datetime('now'))
        """
        account_id = execute_update(sql, (username, password, mac, imei, address, remark))

        # 记录日志
        actor = getattr(request, 'user', {})
        LogService.log_operation(
            action='account_create',
            message=f'创建账户 {username}',
            user_id=actor.get('user_id'),
            username=actor.get('username')
        )
        
        return jsonify({
            'message': '账户创建成功',
            'id': account_id
        }), 201
        
    except Exception as e:
        logger.error(f'创建账户异常: {e}')
        return jsonify({'error': f'系统异常: {str(e)}'}), 500


@account_bp.route('/accounts/<int:account_id>', methods=['GET', 'PUT', 'DELETE'])
@token_required
def manage_account(account_id):
    """
    管理单个账户（获取、更新、删除）
    """
    # GET - 获取账户信息
    if request.method == 'GET':
        try:
            sql = "SELECT id, username, password, mac, imei, address, remark, status, created_at FROM accounts WHERE id = ?"
            account = execute_query(sql, (account_id,), fetch_one=True)
            
            if not account:
                return jsonify({'error': '账户不存在'}), 404
            
            return jsonify({'data': account}), 200
            
        except Exception as e:
            logger.error(f'获取账户信息异常: {e}')
            return jsonify({'error': f'系统异常: {str(e)}'}), 500
    
    # PUT - 更新账户信息
    elif request.method == 'PUT':
        try:
            data = request.json
            
            # 检查账户是否存在
            check_sql = "SELECT id FROM accounts WHERE id = ?"
            existing = execute_query(check_sql, (account_id,))
            if not existing:
                return jsonify({'error': '账户不存在'}), 404
            
            # 构建更新SQL
            update_fields = []
            params = []
            
            if 'username' in data:
                username = data['username'].strip()
                if username:
                    # 检查用户名是否已被其他账户使用
                    check_username_sql = "SELECT id FROM accounts WHERE username = ? AND id != ?"
                    username_exists = execute_query(check_username_sql, (username, account_id))
                    if username_exists:
                        return jsonify({'error': '用户名已存在'}), 400
                    update_fields.append('username = ?')
                    params.append(username)
            
            if 'password' in data:
                password = data['password'].strip()
                if password:
                    # 直接存储密码，不进行加密
                    update_fields.append('password = ?')
                    params.append(password)
            
            if 'mac' in data:
                update_fields.append('mac = ?')
                params.append(data['mac'].strip())
            
            if 'imei' in data:
                update_fields.append('imei = ?')
                params.append(data['imei'].strip() if data['imei'] else None)
            
            if 'address' in data:
                update_fields.append('address = ?')
                params.append(data['address'].strip() if data['address'] else None)
            
            if 'remark' in data:
                update_fields.append('remark = ?')
                params.append(data['remark'].strip() if data['remark'] else None)
            
            if 'status' in data:
                status_raw = str(data['status']).strip()
                if status_raw not in ('0', '1'):
                    return jsonify({'error': '状态值无效，应为0或1'}), 400
                update_fields.append('status = ?')
                params.append(int(status_raw))
            
            if not update_fields:
                return jsonify({'error': '没有要更新的字段'}), 400
            
            update_fields.append('updated_at = datetime("now")')
            params.append(account_id)
            
            sql = f"UPDATE accounts SET {', '.join(update_fields)} WHERE id = ?"
            execute_update(sql, tuple(params))

            actor = getattr(request, 'user', {})
            LogService.log_operation(
                action='account_update',
                message=f'更新账户 {account_id}',
                user_id=actor.get('user_id'),
                username=actor.get('username')
            )
            
            return jsonify({'message': '账户更新成功'}), 200
            
        except Exception as e:
            logger.error(f'更新账户异常: {e}')
            return jsonify({'error': f'系统异常: {str(e)}'}), 500
    
    # DELETE - 删除账户
    elif request.method == 'DELETE':
        try:
            # 检查账户是否存在
            check_sql = "SELECT id FROM accounts WHERE id = ?"
            existing = execute_query(check_sql, (account_id,))
            if not existing:
                return jsonify({'error': '账户不存在'}), 404
            
            # 删除账户
            sql = "DELETE FROM accounts WHERE id = ?"
            execute_update(sql, (account_id,))

            actor = getattr(request, 'user', {})
            LogService.log_operation(
                action='account_delete',
                message=f'删除账户 {account_id}',
                user_id=actor.get('user_id'),
                username=actor.get('username')
            )
            
            return jsonify({'message': '账户删除成功'}), 200
            
        except Exception as e:
            logger.error(f'删除账户异常: {e}')
            return jsonify({'error': f'系统异常: {str(e)}'}), 500


@account_bp.route('/stats', methods=['GET'])
@token_required
def get_stats():
    """
    获取统计数据
    
    Response:
    {
        "total_accounts": 10,
        "active_accounts": 8,
        "total_sources": 5,
        "total_channels": 1250
    }
    """
    try:
        # 总账户数
        total_accounts_sql = "SELECT COUNT(*) as count FROM accounts"
        total_accounts = execute_query(total_accounts_sql, ())[0]['count']
        
        # 活跃账户数
        active_accounts_sql = "SELECT COUNT(*) as count FROM accounts WHERE status = 0"
        active_accounts = execute_query(active_accounts_sql, ())[0]['count']
        
        # 总直播源数（从channels表中统计不同的source_id）
        total_sources_sql = "SELECT COUNT(DISTINCT source_id) as count FROM channels"
        sources_result = execute_query(total_sources_sql, ())
        total_sources = sources_result[0]['count'] if sources_result else 0
        
        # 总频道数
        total_channels_sql = "SELECT COUNT(*) as count FROM channels"
        channels_result = execute_query(total_channels_sql, ())
        total_channels = channels_result[0]['count'] if channels_result else 0
        
        return jsonify({
            'total_accounts': total_accounts,
            'active_accounts': active_accounts,
            'total_sources': total_sources,
            'total_channels': total_channels
        }), 200
        
    except Exception as e:
        logger.error(f'获取统计数据异常: {e}')
        return jsonify({'error': f'系统异常: {str(e)}'}), 500


@account_bp.route('/sources', methods=['GET'])
@token_required
def get_sources():
    """
    获取直播源列表
    """
    try:
        sql = """
            SELECT 
                s.id,
                s.name,
                s.status,
                s.channel_count,
                s.last_updated,
                s.created_at,
                a.username as account_name
            FROM sources s
            LEFT JOIN accounts a ON s.account_id = a.id
            ORDER BY s.created_at DESC
        """
        sources = execute_query(sql, ())
        
        return jsonify({
            'data': sources
        }), 200
        
    except Exception as e:
        logger.error(f'获取直播源列表异常: {e}')
        return jsonify({'error': f'系统异常: {str(e)}'}), 500


@account_bp.route('/sources/fetch', methods=['POST'])
@token_required
def fetch_source():
    """
    获取直播源（调用IPTV服务）
    """
    try:
        from app.services.iptv_service import IPTVService
        
        data = request.json
        account_id = data.get('account_id')
        
        if not account_id:
            return jsonify({'error': '账户ID不能为空'}), 400
        
        # 调用IPTV服务获取频道
        result = IPTVService.fetch_channels(account_id)
        
        if result.get('success'):
            return jsonify({
                'data': result
            }), 200
        else:
            return jsonify({
                'error': result.get('message', '获取失败')
            }), 400
        
    except Exception as e:
        logger.error(f'获取直播源异常: {e}')
        return jsonify({'error': f'系统异常: {str(e)}'}), 500


@account_bp.route('/sources/<int:source_id>', methods=['DELETE'])
@token_required
def delete_source(source_id):
    """
    删除直播源及其所有频道
    """
    try:
        # 检查源是否存在
        check_sql = "SELECT id FROM sources WHERE id = ?"
        existing = execute_query(check_sql, (source_id,))
        if not existing:
            return jsonify({'error': '直播源不存在'}), 404
        
        # 删除关联的频道
        delete_channels_sql = "DELETE FROM channels WHERE source_id = ?"
        execute_update(delete_channels_sql, (source_id,))
        
        # 删除源
        delete_source_sql = "DELETE FROM sources WHERE id = ?"
        execute_update(delete_source_sql, (source_id,))
        
        return jsonify({'message': '直播源删除成功'}), 200
        
    except Exception as e:
        logger.error(f'删除直播源异常: {e}')
        return jsonify({'error': f'系统异常: {str(e)}'}), 500


@account_bp.route('/channels', methods=['GET'])
@token_required
def get_channels():
    """
    获取频道列表
    
    Query Params:
    - account_id: 账户ID（可选）
    """
    try:
        account_id = request.args.get('account_id')
        
        if account_id:
            sql = """
                SELECT 
                    c.id,
                    c.channel_id,
                    c.channel_name,
                    c.category,
                    c.status,
                    c.created_at,
                    a.username as account_name
                FROM channels c
                LEFT JOIN sources s ON c.source_id = s.id
                LEFT JOIN accounts a ON s.account_id = a.id
                WHERE s.account_id = ?
                ORDER BY c.created_at DESC
            """
            channels = execute_query(sql, (account_id,))
        else:
            sql = """
                SELECT 
                    c.id,
                    c.channel_id,
                    c.channel_name,
                    c.category,
                    c.status,
                    c.created_at,
                    a.username as account_name
                FROM channels c
                LEFT JOIN sources s ON c.source_id = s.id
                LEFT JOIN accounts a ON s.account_id = a.id
                ORDER BY c.created_at DESC
            """
            channels = execute_query(sql, ())
        
        return jsonify({
            'data': channels
        }), 200
        
    except Exception as e:
        logger.error(f'获取频道列表异常: {e}')
        return jsonify({'error': f'系统异常: {str(e)}'}), 500


@account_bp.route('/channels/<int:channel_id>', methods=['GET', 'PUT', 'DELETE'])
@token_required
def manage_channel(channel_id):
    """
    获取、更新或删除单个频道
    - GET: 获取频道详情
    - PUT: 更新频道名称/分类/状态
    - DELETE: 删除频道
    """
    if request.method == 'GET':
        try:
            sql = """
                SELECT id, channel_id, channel_name, channel_url, category, status, source_id, created_at, updated_at
                FROM channels
                WHERE id = ?
            """
            channel = execute_query(sql, (channel_id,), fetch_one=True)
            if not channel:
                return jsonify({'error': '频道不存在'}), 404
            return jsonify({'data': channel}), 200
        except Exception as e:
            logger.error(f'获取频道异常: {e}')
            return jsonify({'error': f'系统异常: {str(e)}'}), 500
    
    if request.method == 'PUT':
        try:
            data = request.json or {}
            check_sql = "SELECT id FROM channels WHERE id = ?"
            existing = execute_query(check_sql, (channel_id,))
            if not existing:
                return jsonify({'error': '频道不存在'}), 404
            update_fields = []
            params = []
            if 'channel_name' in data:
                name = data['channel_name'].strip()
                if name:
                    update_fields.append('channel_name = ?')
                    params.append(name)
            if 'category' in data:
                category = data['category'].strip() if data['category'] else None
                update_fields.append('category = ?')
                params.append(category)
            if 'status' in data:
                status_raw = str(data['status']).strip()
                if status_raw not in ('0', '1'):
                    return jsonify({'error': '状态值无效，应为0或1'}), 400
                update_fields.append('status = ?')
                params.append(int(status_raw))
            if not update_fields:
                return jsonify({'error': '没有要更新的字段'}), 400
            update_fields.append('updated_at = datetime("now")')
            params.append(channel_id)
            sql = f"UPDATE channels SET {', '.join(update_fields)} WHERE id = ?"
            execute_update(sql, tuple(params))
            return jsonify({'message': '频道更新成功'}), 200
        except Exception as e:
            logger.error(f'更新频道异常: {e}')
            return jsonify({'error': f'系统异常: {str(e)}'}), 500
    
    # DELETE
    try:
        check_sql = "SELECT id FROM channels WHERE id = ?"
        existing = execute_query(check_sql, (channel_id,))
        if not existing:
            return jsonify({'error': '频道不存在'}), 404
        sql = "DELETE FROM channels WHERE id = ?"
        execute_update(sql, (channel_id,))
        return jsonify({'message': '频道删除成功'}), 200
    except Exception as e:
        logger.error(f'删除频道异常: {e}')
        return jsonify({'error': f'系统异常: {str(e)}'}), 500


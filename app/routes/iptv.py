"""
IPTV 直播源 API 路由
"""

from flask import Blueprint, request, jsonify
from app.utils.auth import token_required
from app.services.iptv_service import IPTVService
from app.services import LogService
from app.utils import get_logger

logger = get_logger('iptv_routes')

iptv_bp = Blueprint('iptv', __name__, url_prefix='/api/iptv')


@iptv_bp.route('/fetch', methods=['POST'])
@token_required
def fetch_channels():
    """
    获取并保存 IPTV 频道
    
    Request Body:
    {
        "account_id": 1,
        "filter_sd": true,          // 可选，是否过滤标清频道
        "channel_filters": []       // 可选，频道名称过滤器（正则表达式）
    }
    
    Response:
    {
        "success": true,
        "message": "成功保存 100 个频道",
        "channel_count": 100
    }
    """
    try:
        data = request.get_json()
        account_id = data.get('account_id')
        
        if not account_id:
            return jsonify({
                'success': False,
                'message': '缺少 account_id 参数'
            }), 400
        
        filter_sd = data.get('filter_sd', True)
        channel_filters = data.get('channel_filters', None)
        
        # 调用服务层
        result = IPTVService.fetch_and_save_channels(
            account_id=account_id,
            filter_sd=filter_sd,
            channel_filters=channel_filters
        )
        actor = getattr(request, 'user', {})
        LogService.log_operation(
            action='channel_fetch',
            message=f"获取频道 account_id={account_id} -> {result.get('message', '')}",
            user_id=actor.get('user_id'),
            username=actor.get('username'),
            status='success' if result.get('success') else 'failed'
        )

        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f'获取频道异常: {e}')
        return jsonify({
            'success': False,
            'message': f'系统异常: {str(e)}'
        }), 500


@iptv_bp.route('/channels/<int:source_id>', methods=['GET'])
@token_required
def get_channels(source_id):
    """
    获取直播源的所有频道
    
    Query Params:
    - status: 频道状态（可选，1: 启用, 0: 禁用）
    
    Response:
    {
        "success": true,
        "channels": [
            {
                "id": 1,
                "channel_id": "1",
                "channel_name": "CCTV1高清",
                "channel_url": "rtsp://...",
                "channel_logo_url": "http://...",
                "status": 1,
                "created_at": "2024-01-01 00:00:00",
                "updated_at": "2024-01-01 00:00:00"
            }
        ]
    }
    """
    try:
        status = request.args.get('status', type=int)
        
        channels = IPTVService.get_channels_by_source(source_id, status)
        
        return jsonify({
            'success': True,
            'channels': channels
        }), 200
        
    except Exception as e:
        logger.error(f'获取频道列表异常: {e}')
        return jsonify({
            'success': False,
            'message': f'系统异常: {str(e)}'
        }), 500


@iptv_bp.route('/channels/<int:channel_id>/status', methods=['PUT'])
@token_required
def update_channel_status(channel_id):
    """
    更新频道状态
    
    Request Body:
    {
        "status": 1  // 1: 启用, 0: 禁用
    }
    
    Response:
    {
        "success": true,
        "message": "频道状态已更新"
    }
    """
    try:
        data = request.get_json()
        status = data.get('status')
        
        if status not in [0, 1]:
            return jsonify({
                'success': False,
                'message': 'status 必须为 0 或 1'
            }), 400
        
        success = IPTVService.update_channel_status(channel_id, status)
        
        actor = getattr(request, 'user', {})
        if success:
            LogService.log_operation(
                action='channel_status',
                message=f'更新频道 {channel_id} 状态为 {status}',
                user_id=actor.get('user_id'),
                username=actor.get('username'),
                status='success'
            )
            return jsonify({
                'success': True,
                'message': '频道状态已更新'
            }), 200
        else:
            LogService.log_operation(
                action='channel_status',
                message=f'更新频道 {channel_id} 状态失败',
                user_id=actor.get('user_id'),
                username=actor.get('username'),
                status='failed'
            )
            return jsonify({
                'success': False,
                'message': '更新失败'
            }), 400
        
    except Exception as e:
        logger.error(f'更新频道状态异常: {e}')
        return jsonify({
            'success': False,
            'message': f'系统异常: {str(e)}'
        }), 500


@iptv_bp.route('/channels/source/<int:source_id>', methods=['DELETE'])
@token_required
def delete_channels(source_id):
    """
    删除直播源的所有频道
    
    Response:
    {
        "success": true,
        "message": "频道已删除"
    }
    """
    try:
        success = IPTVService.delete_channels_by_source(source_id)
        actor = getattr(request, 'user', {})
        
        if success:
            LogService.log_operation(
                action='channel_delete_all',
                message=f'删除源 {source_id} 关联频道',
                user_id=actor.get('user_id'),
                username=actor.get('username'),
                status='success'
            )
            return jsonify({
                'success': True,
                'message': '频道已删除'
            }), 200
        else:
            LogService.log_operation(
                action='channel_delete_all',
                message=f'删除源 {source_id} 关联频道失败',
                user_id=actor.get('user_id'),
                username=actor.get('username'),
                status='failed'
            )
            return jsonify({
                'success': False,
                'message': '删除失败'
            }), 400
        
    except Exception as e:
        logger.error(f'删除频道异常: {e}')
        return jsonify({
            'success': False,
            'message': f'系统异常: {str(e)}'
        }), 500


@iptv_bp.route('/statistics/<int:source_id>', methods=['GET'])
@token_required
def get_statistics(source_id):
    """
    获取频道统计信息
    
    Response:
    {
        "success": true,
        "statistics": {
            "total": 100,
            "active": 90,
            "inactive": 10
        }
    }
    """
    try:
        stats = IPTVService.get_channel_statistics(source_id)
        
        return jsonify({
            'success': True,
            'statistics': stats
        }), 200
        
    except Exception as e:
        logger.error(f'获取统计信息异常: {e}')
        return jsonify({
            'success': False,
            'message': f'系统异常: {str(e)}'
        }), 500


@iptv_bp.route('/accounts', methods=['GET'])
@token_required
def get_accounts():
    """
    获取账户列表
    
    Response:
    {
        "success": true,
        "accounts": [
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
        from app.utils import execute_query
        
        sql = """
            SELECT id, username, mac, imei, address, status, created_at
            FROM accounts
            ORDER BY created_at DESC
        """
        accounts = execute_query(sql, ())
        
        return jsonify({
            'success': True,
            'accounts': accounts,
            'count': len(accounts)
        }), 200
        
    except Exception as e:
        logger.error(f'获取账户列表异常: {e}')
        return jsonify({
            'success': False,
            'message': f'系统异常: {str(e)}'
        }), 500


@iptv_bp.route('/channels/export', methods=['GET'])
@token_required
def export_channels():
    """
    导出频道列表为文本格式
    
    Query Params:
    - source_id: 源ID（可选，不传则导出所有）
    - category: 分类（可选，不传则导出所有）
    
    Response:
    返回文本格式：
    央视,#genre#
    CCTV1,rtsp://xxx
    CCTV2,rtsp://xxx
    广东,#genre#
    ...
    """
    try:
        from app.utils import execute_query
        
        source_id = request.args.get('source_id', type=int)
        category = request.args.get('category')
        
        # 构建查询SQL
        sql = """
            SELECT channel_name, channel_url, category
            FROM channels
            WHERE 1=1
        """
        params = []
        
        if source_id:
            sql += " AND source_id = ?"
            params.append(source_id)
        
        if category:
            sql += " AND category = ?"
            params.append(category)
        
        sql += " ORDER BY category, channel_name"
        
        channels = execute_query(sql, tuple(params))
        
        # 按分类分组
        grouped = {}
        for channel in channels:
            cat = channel['category'] or '未分类'
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append(channel)
        
        # 生成文本内容
        lines = []
        for cat in sorted(grouped.keys()):
            lines.append(f"{cat},#genre#")
            for channel in grouped[cat]:
                lines.append(f"{channel['channel_name']},{channel['channel_url']}")
        
        text_content = '\n'.join(lines)
        
        # 记录日志
        actor = getattr(request, 'user', {})
        LogService.log_operation(
            action='channel_export',
            message=f'导出频道列表，共 {len(channels)} 个频道',
            user_id=actor.get('user_id'),
            username=actor.get('username')
        )
        
        return text_content, 200, {
            'Content-Type': 'text/plain; charset=utf-8',
            'Content-Disposition': 'attachment; filename=channels.txt'
        }
        
    except Exception as e:
        logger.error(f'导出频道异常: {e}')
        return jsonify({
            'success': False,
            'message': f'系统异常: {str(e)}'
        }), 500

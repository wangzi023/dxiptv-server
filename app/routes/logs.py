"""
日志查询路由
"""
from flask import Blueprint, request, jsonify
from app.services import LogService
from app.utils import token_required

logs_bp = Blueprint('logs', __name__, url_prefix='/api/logs')


@logs_bp.route('', methods=['GET'])
@token_required
def list_logs():
    """分页获取日志列表，支持类型、级别、状态、关键词过滤"""
    try:
        log_type = request.args.get('type')
        level = request.args.get('level')
        status = request.args.get('status')
        keyword = request.args.get('keyword')
        page = request.args.get('page', default=1, type=int)
        page_size = request.args.get('page_size', default=20, type=int)

        result = LogService.query_logs(
            log_type=log_type,
            level=level,
            status=status,
            keyword=keyword,
            page=page,
            page_size=page_size,
        )
        return jsonify({'success': True, **result})
    except Exception as exc:  # noqa: BLE001
        return jsonify({'success': False, 'error': str(exc)}), 500

"""
频道模板管理 API 路由
提供频道模板的增删改查和匹配功能
"""

from flask import Blueprint, request, jsonify
from app.utils.auth import token_required
from app.services.channel_template_service import ChannelTemplateService
from app.utils import get_logger
from app.services import LogService

logger = get_logger('channel_template_routes')

channel_template_bp = Blueprint('channel_template', __name__, url_prefix='/api/channel-template')


@channel_template_bp.route('/templates', methods=['GET'])
@token_required
def get_templates():
    """
    获取频道模板列表
    Query Params:
        group_title: 可选，按分组筛选
    """
    try:
        group_title = request.args.get('group_title')
        templates = ChannelTemplateService.get_all_templates(group_title)
        return jsonify({'success': True, 'data': templates}), 200
    except Exception as e:
        logger.error(f'获取频道模板异常: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@channel_template_bp.route('/templates/<int:template_id>', methods=['GET'])
@token_required
def get_template(template_id):
    """获取单个模板"""
    try:
        template = ChannelTemplateService.get_template_by_id(template_id)
        if template:
            return jsonify({'success': True, 'data': template}), 200
        else:
            return jsonify({'success': False, 'message': '模板不存在'}), 404
    except Exception as e:
        logger.error(f'获取模板异常: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@channel_template_bp.route('/groups', methods=['GET'])
@token_required
def get_groups():
    """获取所有分组"""
    try:
        groups = ChannelTemplateService.get_all_groups()
        return jsonify({'success': True, 'data': groups}), 200
    except Exception as e:
        logger.error(f'获取分组异常: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@channel_template_bp.route('/statistics', methods=['GET'])
@token_required
def get_statistics():
    """获取统计信息"""
    try:
        stats = ChannelTemplateService.get_statistics()
        return jsonify({'success': True, 'data': stats}), 200
    except Exception as e:
        logger.error(f'获取统计异常: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@channel_template_bp.route('/templates', methods=['POST'])
@token_required
def add_template():
    """添加频道模板"""
    try:
        data = request.get_json()
        
        channel_id = data.get('channel_id')
        name = data.get('name')
        group_title = data.get('group_title')
        
        if not all([channel_id, name, group_title]):
            return jsonify({'success': False, 'message': '缺少必要参数'}), 400
        
        result = ChannelTemplateService.add_template(channel_id, name, group_title)
        
        # 记录日志
        if result['success']:
            actor = getattr(request, 'user', {})
            LogService.log_operation(
                action='template_add',
                message=f'添加频道模板: {name} ({channel_id})',
                user_id=actor.get('user_id'),
                username=actor.get('username')
            )
        
        status_code = 201 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f'添加模板异常: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@channel_template_bp.route('/templates/<int:template_id>', methods=['PUT'])
@token_required
def update_template(template_id):
    """更新频道模板"""
    try:
        data = request.get_json()
        
        channel_id = data.get('channel_id')
        name = data.get('name')
        group_title = data.get('group_title')
        
        result = ChannelTemplateService.update_template(
            template_id,
            channel_id=channel_id,
            name=name,
            group_title=group_title
        )
        
        # 记录日志
        if result['success']:
            actor = getattr(request, 'user', {})
            LogService.log_operation(
                action='template_update',
                message=f'更新频道模板: ID={template_id}',
                user_id=actor.get('user_id'),
                username=actor.get('username')
            )
        
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f'更新模板异常: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@channel_template_bp.route('/templates/<int:template_id>', methods=['DELETE'])
@token_required
def delete_template(template_id):
    """删除频道模板"""
    try:
        result = ChannelTemplateService.delete_template(template_id)
        
        # 记录日志
        if result['success']:
            actor = getattr(request, 'user', {})
            LogService.log_operation(
                action='template_delete',
                message=f'删除频道模板: ID={template_id}',
                user_id=actor.get('user_id'),
                username=actor.get('username')
            )
        
        status_code = 200 if result['success'] else 404
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f'删除模板异常: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@channel_template_bp.route('/match/<channel_id>', methods=['GET'])
@token_required
def match_channel(channel_id):
    """匹配频道信息"""
    try:
        info = ChannelTemplateService.match_channel_info(channel_id)
        return jsonify({'success': True, 'data': info}), 200
    except Exception as e:
        logger.error(f'匹配频道异常: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

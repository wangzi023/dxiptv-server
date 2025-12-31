"""
定时任务路由
"""

from flask import Blueprint, request, jsonify
from app.services import ScheduleService, LogService
from app.utils import token_required
from app.utils import get_logger

schedule_bp = Blueprint('schedule', __name__, url_prefix='/api/schedule')
logger = get_logger('schedule_routes')


@schedule_bp.route('/tasks', methods=['POST'])
@token_required
def create_task():
    """创建定时任务"""
    try:
        data = request.json
        
        # 验证必填字段
        required_fields = ['account_id', 'task_type', 'schedule_time']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'缺少必填字段: {field}'}), 400
        
        account_id = data.get('account_id')
        task_type = data.get('task_type')
        schedule_time = data.get('schedule_time')
        repeat_type = data.get('repeat_type', 'daily')
        filter_sd = data.get('filter_sd', True)
        channel_filters = data.get('channel_filters')
        is_enabled = data.get('is_enabled', True)
        
        # 验证时间格式
        if not _is_valid_time_format(schedule_time):
            return jsonify({'error': '时间格式不正确，应为 HH:MM'}), 400
        
        # 验证重复类型
        valid_repeat_types = ['once', 'daily', 'weekly', 'monthly']
        if repeat_type not in valid_repeat_types:
            return jsonify({'error': f'无效的重复类型: {repeat_type}'}), 400
        
        result = ScheduleService.create_task(
            account_id=account_id,
            task_type=task_type,
            schedule_time=schedule_time,
            repeat_type=repeat_type,
            filter_sd=filter_sd,
            channel_filters=channel_filters,
            is_enabled=is_enabled
        )
        if result['success']:
            actor = getattr(request, 'user', {})
            LogService.log_operation(
                action='schedule_create',
                message=f"创建任务 account={account_id} type={task_type}",
                user_id=actor.get('user_id'),
                username=actor.get('username')
            )

        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f'创建定时任务异常: {e}')
        return jsonify({'error': str(e)}), 500


@schedule_bp.route('/tasks', methods=['GET'])
@token_required
def get_tasks():
    """获取定时任务列表"""
    try:
        account_id = request.args.get('account_id', type=int)
        
        tasks = ScheduleService.get_all_tasks(account_id=account_id)
        
        return jsonify({
            'success': True,
            'message': '获取任务列表成功',
            'tasks': tasks,
            'count': len(tasks)
        }), 200
    
    except Exception as e:
        logger.error(f'获取定时任务列表异常: {e}')
        return jsonify({'error': str(e)}), 500


@schedule_bp.route('/tasks/<int:task_id>', methods=['GET'])
@token_required
def get_task(task_id):
    """获取单个定时任务"""
    try:
        task = ScheduleService.get_task(task_id)
        
        if not task:
            return jsonify({'error': '任务不存在'}), 404
        
        return jsonify({
            'success': True,
            'message': '获取任务成功',
            'task': task
        }), 200
    
    except Exception as e:
        logger.error(f'获取定时任务异常: {e}')
        return jsonify({'error': str(e)}), 500


@schedule_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@token_required
def update_task(task_id):
    """更新定时任务"""
    try:
        data = request.json
        
        # 验证时间格式（如果更新了 schedule_time）
        if 'schedule_time' in data:
            if not _is_valid_time_format(data['schedule_time']):
                return jsonify({'error': '时间格式不正确，应为 HH:MM'}), 400
        
        # 验证重复类型
        if 'repeat_type' in data:
            valid_repeat_types = ['once', 'daily', 'weekly', 'monthly']
            if data['repeat_type'] not in valid_repeat_types:
                return jsonify({'error': f'无效的重复类型: {data["repeat_type"]}'}), 400
        
        result = ScheduleService.update_task(task_id, **data)
        if result['success']:
            actor = getattr(request, 'user', {})
            LogService.log_operation(
                action='schedule_update',
                message=f'更新任务 {task_id}',
                user_id=actor.get('user_id'),
                username=actor.get('username')
            )

        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f'更新定时任务异常: {e}')
        return jsonify({'error': str(e)}), 500


@schedule_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@token_required
def delete_task(task_id):
    """删除定时任务"""
    try:
        result = ScheduleService.delete_task(task_id)
        if result['success']:
            actor = getattr(request, 'user', {})
            LogService.log_operation(
                action='schedule_delete',
                message=f'删除任务 {task_id}',
                user_id=actor.get('user_id'),
                username=actor.get('username')
            )

        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f'删除定时任务异常: {e}')
        return jsonify({'error': str(e)}), 500


@schedule_bp.route('/tasks/<int:task_id>/enable', methods=['PUT'])
@token_required
def enable_task(task_id):
    """启用定时任务"""
    try:
        result = ScheduleService.enable_task(task_id)
        if result['success']:
            actor = getattr(request, 'user', {})
            LogService.log_operation(
                action='schedule_enable',
                message=f'启用任务 {task_id}',
                user_id=actor.get('user_id'),
                username=actor.get('username')
            )

        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f'启用定时任务异常: {e}')
        return jsonify({'error': str(e)}), 500


@schedule_bp.route('/tasks/<int:task_id>/disable', methods=['PUT'])
@token_required
def disable_task(task_id):
    """禁用定时任务"""
    try:
        result = ScheduleService.disable_task(task_id)
        if result['success']:
            actor = getattr(request, 'user', {})
            LogService.log_operation(
                action='schedule_disable',
                message=f'禁用任务 {task_id}',
                user_id=actor.get('user_id'),
                username=actor.get('username')
            )

        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f'禁用定时任务异常: {e}')
        return jsonify({'error': str(e)}), 500


@schedule_bp.route('/tasks/<int:task_id>/status', methods=['GET'])
@token_required
def get_task_status(task_id):
    """获取定时任务状态"""
    try:
        result = ScheduleService.get_task_status(task_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
    
    except Exception as e:
        logger.error(f'获取定时任务状态异常: {e}')
        return jsonify({'error': str(e)}), 500


@schedule_bp.route('/tasks/<int:task_id>/execute', methods=['POST'])
@token_required
def execute_task_now(task_id):
    """立即执行定时任务"""
    try:
        from app.utils.scheduler import get_scheduler
        from app.services.iptv_service import IPTVService
        import traceback
        
        # 获取任务信息
        task = ScheduleService.get_task(task_id)
        if not task:
            return jsonify({'error': '任务不存在'}), 404
        
        actor = getattr(request, 'user', {})
        
        # 记录任务开始执行
        LogService.log_task(
            task_id=task_id,
            account_id=task['account_id'],
            task_type=task['task_type'],
            status='running',
            message='用户手动触发任务执行'
        )
        
        try:
            # 执行任务
            if task['task_type'] == 'fetch_channels':
                logger.info(f'执行任务 {task_id}（账户 {task["account_id"]}，类型 {task["task_type"]}）')
                result = IPTVService.fetch_and_save_channels(
                    account_id=task['account_id'],
                    filter_sd=task.get('filter_sd', True),
                    channel_filters=task.get('channel_filters')
                )
                logger.info(f'任务 {task_id} 执行结果: {result}')
                
                # 记录执行结果
                status = 'success' if result.get('success') else 'failed'
                LogService.log_task(
                    task_id=task_id,
                    account_id=task['account_id'],
                    task_type=task['task_type'],
                    status=status,
                    message=result.get('message', '')
                )
                
                # 记录操作日志
                LogService.log_operation(
                    action='schedule_execute',
                    message=f'手动执行任务 {task_id}（{task["task_type"]}）：{result.get("message", "")}',
                    user_id=actor.get('user_id'),
                    username=actor.get('username'),
                    status=status
                )
                
                # 更新任务执行记录
                ScheduleService.record_execution(task_id, result.get('success', False), result.get('message'))
                
                return jsonify({
                    'success': result.get('success', False),
                    'message': result.get('message', '任务执行失败'),
                    'result': result
                }), 200 if result.get('success') else 400
            else:
                return jsonify({'error': f'不支持的任务类型: {task["task_type"]}'}), 400
        
        except Exception as e:
            # 捕获完整的异常堆栈
            error_trace = traceback.format_exc()
            logger.error(f'任务 {task_id} 执行异常:\n{error_trace}')
            
            # 记录执行失败
            LogService.log_task(
                task_id=task_id,
                account_id=task['account_id'],
                task_type=task['task_type'],
                status='failed',
                message=f'任务执行异常: {str(e)}'
            )
            
            LogService.log_operation(
                action='schedule_execute',
                message=f'手动执行任务 {task_id} 异常: {str(e)}',
                user_id=actor.get('user_id'),
                username=actor.get('username'),
                status='failed'
            )
            
            ScheduleService.record_execution(task_id, False, str(e))
            
            return jsonify({'error': f'任务执行失败: {str(e)}'}), 500
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f'手动执行定时任务异常: {error_trace}')
        actor = getattr(request, 'user', {})
        LogService.log_operation(
            action='schedule_execute',
            message=f'手动执行任务 {task_id} 异常: {str(e)}',
            user_id=actor.get('user_id'),
            username=actor.get('username'),
            status='failed'
        )
        return jsonify({'error': str(e)}), 500


def _is_valid_time_format(time_str):
    """验证时间格式 (HH:MM)"""
    try:
        if isinstance(time_str, str):
            parts = time_str.split(':')
            if len(parts) != 2:
                return False
            hour = int(parts[0])
            minute = int(parts[1])
            return 0 <= hour <= 23 and 0 <= minute <= 59
        return False
    except (ValueError, AttributeError):
        return False

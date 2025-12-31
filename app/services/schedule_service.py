"""
定时任务管理服务
"""

from app.utils import execute_query, execute_update, get_logger
from app.utils.scheduler import Task, get_scheduler

logger = get_logger('schedule_service')


class ScheduleService:
    """定时任务管理服务"""
    
    @staticmethod
    def create_task(account_id, task_type, schedule_time, repeat_type='daily', 
                   filter_sd=True, channel_filters=None, is_enabled=True):
        """
        创建定时任务
        
        Args:
            account_id: 账户 ID
            task_type: 任务类型 (fetch_channels 等)
            schedule_time: 调度时间 (HH:MM 格式)
            repeat_type: 重复类型 (once, daily, weekly, monthly)
            filter_sd: 是否过滤标清频道
            channel_filters: 频道过滤器 (JSON 字符串)
            is_enabled: 是否启用
            
        Returns:
            dict: 任务信息
        """
        try:
            # 插入数据库
            sql = """
                INSERT INTO schedule_tasks 
                (account_id, task_type, schedule_time, repeat_type, filter_sd, 
                 channel_filters, is_enabled, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """
            
            execute_update(sql, (
                account_id, task_type, schedule_time, repeat_type,
                1 if filter_sd else 0, channel_filters, 1 if is_enabled else 0
            ))
            
            # 获取插入的任务
            task = ScheduleService.get_latest_task(account_id, task_type)
            
            # 添加到调度器
            if task:
                scheduler = get_scheduler()
                task_obj = Task(
                    task_id=task['id'],
                    task_type=task_type,
                    account_id=account_id,
                    schedule_time=schedule_time,
                    is_enabled=is_enabled,
                    repeat_type=repeat_type,
                    filter_sd=filter_sd,
                    channel_filters=channel_filters
                )
                scheduler.add_task(task_obj)
            
            return {
                'success': True,
                'message': '任务创建成功',
                'task': task
            }
        except Exception as e:
            logger.error(f'创建定时任务异常: {e}')
            return {
                'success': False,
                'message': f'创建任务失败: {e}'
            }
    
    @staticmethod
    def get_task(task_id):
        """获取任务"""
        sql = """
            SELECT id, account_id, task_type, schedule_time, repeat_type,
                   filter_sd, channel_filters, is_enabled, last_executed,
                   next_execution, execution_count, last_error, created_at, updated_at
            FROM schedule_tasks
            WHERE id = ?
        """
        result = execute_query(sql, (task_id,), fetch_one=True)
        return result
    
    @staticmethod
    def get_latest_task(account_id, task_type):
        """获取最新创建的任务"""
        sql = """
            SELECT id, account_id, task_type, schedule_time, repeat_type,
                   filter_sd, channel_filters, is_enabled, last_executed,
                   next_execution, execution_count, last_error, created_at, updated_at
            FROM schedule_tasks
            WHERE account_id = ? AND task_type = ?
            ORDER BY created_at DESC
            LIMIT 1
        """
        result = execute_query(sql, (account_id, task_type), fetch_one=True)
        return result
    
    @staticmethod
    def get_all_tasks(account_id=None):
        """获取所有任务"""
        if account_id:
            sql = """
                SELECT id, account_id, task_type, schedule_time, repeat_type,
                       filter_sd, channel_filters, is_enabled, last_executed,
                       next_execution, execution_count, last_error, created_at, updated_at
                FROM schedule_tasks
                WHERE account_id = ?
                ORDER BY created_at DESC
            """
            return execute_query(sql, (account_id,))
        else:
            sql = """
                SELECT id, account_id, task_type, schedule_time, repeat_type,
                       filter_sd, channel_filters, is_enabled, last_executed,
                       next_execution, execution_count, last_error, created_at, updated_at
                FROM schedule_tasks
                ORDER BY created_at DESC
            """
            return execute_query(sql, ())
    
    @staticmethod
    def update_task(task_id, **kwargs):
        """更新任务"""
        try:
            allowed_fields = {
                'schedule_time', 'repeat_type', 'filter_sd', 
                'channel_filters', 'is_enabled'
            }
            
            updates = {}
            for key, value in kwargs.items():
                if key in allowed_fields:
                    updates[key] = value
            
            if not updates:
                return {
                    'success': False,
                    'message': '没有要更新的字段'
                }
            
            # 构建 SQL
            set_clause = ', '.join([f'{k} = ?' for k in updates.keys()])
            values = list(updates.values()) + [task_id]
            
            sql = f"""
                UPDATE schedule_tasks
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """
            
            execute_update(sql, values)
            
            # 更新调度器中的任务
            scheduler = get_scheduler()
            task = scheduler.get_task(task_id)
            if task:
                for key, value in updates.items():
                    if key == 'is_enabled':
                        task.is_enabled = value == 1 or value is True
                    elif key == 'filter_sd':
                        task.filter_sd = value == 1 or value is True
                    else:
                        setattr(task, key, value)
            
            return {
                'success': True,
                'message': '任务更新成功'
            }
        except Exception as e:
            logger.error(f'更新定时任务异常: {e}')
            return {
                'success': False,
                'message': f'更新任务失败: {e}'
            }
    
    @staticmethod
    def delete_task(task_id):
        """删除任务"""
        try:
            sql = "DELETE FROM schedule_tasks WHERE id = ?"
            execute_update(sql, (task_id,))
            
            # 从调度器中移除
            scheduler = get_scheduler()
            scheduler.remove_task(task_id)
            
            return {
                'success': True,
                'message': '任务删除成功'
            }
        except Exception as e:
            logger.error(f'删除定时任务异常: {e}')
            return {
                'success': False,
                'message': f'删除任务失败: {e}'
            }
    
    @staticmethod
    def enable_task(task_id):
        """启用任务"""
        return ScheduleService.update_task(task_id, is_enabled=True)
    
    @staticmethod
    def disable_task(task_id):
        """禁用任务"""
        return ScheduleService.update_task(task_id, is_enabled=False)
    
    @staticmethod
    def get_task_status(task_id):
        """获取任务状态"""
        task = ScheduleService.get_task(task_id)
        if not task:
            return {
                'success': False,
                'message': '任务不存在'
            }
        
        return {
            'success': True,
            'task': task
        }

    @staticmethod
    def record_execution(task_id, success: bool, message: str = None):
        """记录任务执行结果到数据库"""
        sql = (
            """
            UPDATE schedule_tasks
            SET last_executed = CURRENT_TIMESTAMP,
                execution_count = execution_count + 1,
                last_error = ?
            WHERE id = ?
            """
        )
        last_error = None if success else (message or '执行失败')
        execute_update(sql, (last_error, task_id))
    
    @staticmethod
    def sync_tasks_to_scheduler():
        """
        将数据库中的任务同步到调度器
        在应用启动时调用
        """
        try:
            tasks = ScheduleService.get_all_tasks()
            scheduler = get_scheduler()
            
            for task_data in tasks:
                task = Task(
                    task_id=task_data['id'],
                    task_type=task_data['task_type'],
                    account_id=task_data['account_id'],
                    schedule_time=task_data['schedule_time'],
                    is_enabled=bool(task_data['is_enabled']),
                    repeat_type=task_data['repeat_type'],
                    filter_sd=bool(task_data['filter_sd']),
                    channel_filters=task_data.get('channel_filters')
                )
                scheduler.add_task(task)
            
            logger.info(f'从数据库同步了 {len(tasks)} 个定时任务')
            return True
        except Exception as e:
            logger.error(f'同步定时任务异常: {e}')
            return False

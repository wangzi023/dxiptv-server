"""
定时任务调度器 - 用于管理定时执行的任务
"""

import threading
import time
from datetime import datetime, timedelta
from app.utils import get_logger

logger = get_logger('scheduler')


class Task:
    """定时任务类"""
    
    def __init__(self, task_id, task_type, account_id, schedule_time, is_enabled=True, 
                 repeat_type='once', filter_sd=True, channel_filters=None):
        """
        初始化定时任务
        
        Args:
            task_id: 任务 ID
            task_type: 任务类型 (fetch_channels 等)
            account_id: 账户 ID
            schedule_time: 调度时间 (HH:MM 格式或 datetime)
            is_enabled: 是否启用
            repeat_type: 重复类型 (once, daily, weekly, monthly)
            filter_sd: 是否过滤标清频道
            channel_filters: 频道过滤器
        """
        self.task_id = task_id
        self.task_type = task_type
        self.account_id = account_id
        self.is_enabled = is_enabled
        self.repeat_type = repeat_type
        self.filter_sd = filter_sd
        self.channel_filters = channel_filters
        
        # 解析调度时间
        if isinstance(schedule_time, str):
            self.schedule_time = schedule_time  # HH:MM 格式
        else:
            self.schedule_time = schedule_time.strftime('%H:%M')
        
        self.last_executed = None
        self.next_execution = self._calculate_next_execution()
        self.execution_count = 0
        self.last_error = None
    
    def _calculate_next_execution(self):
        """计算下次执行时间"""
        now = datetime.now()
        hour, minute = map(int, self.schedule_time.split(':'))
        
        # 今天的执行时间
        scheduled = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if self.repeat_type == 'once':
            # 仅执行一次，如果时间已过，则不再执行
            if scheduled <= now:
                return None
            return scheduled
        
        elif self.repeat_type == 'daily':
            # 每天执行
            if scheduled <= now:
                scheduled += timedelta(days=1)
            return scheduled
        
        elif self.repeat_type == 'weekly':
            # 每周执行（同一天同一时间）
            if scheduled <= now:
                scheduled += timedelta(weeks=1)
            return scheduled
        
        elif self.repeat_type == 'monthly':
            # 每月执行
            if scheduled <= now:
                # 下个月同一天
                next_month = now.replace(day=1) + timedelta(days=32)
                scheduled = next_month.replace(
                    day=now.day if now.day <= 28 else 28,
                    hour=hour,
                    minute=minute,
                    second=0,
                    microsecond=0
                )
            return scheduled
        
        return scheduled
    
    def should_execute(self):
        """检查是否应该执行"""
        if not self.is_enabled:
            return False
        
        if self.next_execution is None:
            return False
        
        return datetime.now() >= self.next_execution
    
    def mark_executed(self):
        """标记为已执行"""
        self.last_executed = datetime.now()
        self.execution_count += 1
        self.next_execution = self._calculate_next_execution()
        self.last_error = None
    
    def mark_error(self, error):
        """标记执行出错"""
        self.last_error = str(error)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'task_id': self.task_id,
            'task_type': self.task_type,
            'account_id': self.account_id,
            'is_enabled': self.is_enabled,
            'repeat_type': self.repeat_type,
            'schedule_time': self.schedule_time,
            'filter_sd': self.filter_sd,
            'channel_filters': self.channel_filters,
            'last_executed': self.last_executed.isoformat() if self.last_executed else None,
            'next_execution': self.next_execution.isoformat() if self.next_execution else None,
            'execution_count': self.execution_count,
            'last_error': self.last_error
        }


class Scheduler:
    """任务调度器"""
    
    def __init__(self, check_interval=60):
        """
        初始化调度器
        
        Args:
            check_interval: 检查任务的间隔（秒）
        """
        self.tasks = {}
        self.check_interval = check_interval
        self.running = False
        self.thread = None
        self.callbacks = {}  # 任务执行回调
        self.lock = threading.Lock()
    
    def add_task(self, task):
        """添加任务"""
        with self.lock:
            self.tasks[task.task_id] = task
            logger.info(f'添加定时任务: {task.task_id} - {task.schedule_time}')
    
    def remove_task(self, task_id):
        """移除任务"""
        with self.lock:
            if task_id in self.tasks:
                del self.tasks[task_id]
                logger.info(f'移除定时任务: {task_id}')
                return True
        return False
    
    def get_task(self, task_id):
        """获取任务"""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self):
        """获取所有任务"""
        with self.lock:
            return list(self.tasks.values())
    
    def update_task(self, task_id, **kwargs):
        """更新任务属性"""
        with self.lock:
            task = self.tasks.get(task_id)
            if task:
                for key, value in kwargs.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
                logger.info(f'更新定时任务: {task_id}')
                return True
        return False
    
    def register_callback(self, task_type, callback):
        """注册任务执行回调"""
        self.callbacks[task_type] = callback
    
    def start(self):
        """启动调度器"""
        if self.running:
            logger.warning('调度器已在运行')
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info('定时任务调度器已启动')
    
    def stop(self):
        """停止调度器"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info('定时任务调度器已停止')
    
    def _run(self):
        """调度器运行循环"""
        while self.running:
            try:
                self._check_and_execute_tasks()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f'调度器异常: {e}')
                time.sleep(self.check_interval)
    
    def _check_and_execute_tasks(self):
        """检查并执行任务"""
        with self.lock:
            tasks_to_execute = [
                task for task in self.tasks.values()
                if task.should_execute()
            ]
        
        for task in tasks_to_execute:
            try:
                self._execute_task(task)
                task.mark_executed()
            except Exception as e:
                logger.error(f'执行任务 {task.task_id} 失败: {e}')
                task.mark_error(e)
    
    def _execute_task(self, task):
        """执行任务"""
        logger.info(f'执行定时任务: {task.task_id} ({task.task_type})')
        
        # 获取回调函数
        callback = self.callbacks.get(task.task_type)
        if callback:
            callback(task)
        else:
            logger.warning(f'未找到任务类型的回调: {task.task_type}')


# 全局调度器实例
_scheduler = None


def get_scheduler(check_interval=60):
    """获取全局调度器实例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = Scheduler(check_interval)
    return _scheduler


def init_scheduler():
    """初始化调度器"""
    scheduler = get_scheduler()
    scheduler.start()
    return scheduler

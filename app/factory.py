"""
应用工厂 - 创建和配置 Flask 应用
"""
from flask import Flask, send_from_directory
from flask_cors import CORS
from config import get_config
from app.utils import setup_logger, get_logger
from app.models import init_database
from app.routes import register_blueprints
from app.utils.scheduler import init_scheduler, get_scheduler
from app.services import ScheduleService
import os


def create_app(config_name=None):
    """
    应用工厂函数
    
    Args:
        config_name (str): 配置名称 (development, production, testing)
        
    Returns:
        Flask: Flask 应用实例
    """
    # 获取配置
    config = get_config(config_name)
    
    # 创建 Flask 应用
    # 注意：不设置 static_folder，因为我们手动处理静态文件
    app = Flask(__name__)
    
    # 应用配置
    app.config.from_object(config)
    
    # 启用 CORS
    CORS(app)
    
    # 初始化日志（传入日志目录）
    import logging
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    log_level_value = logging.DEBUG if config.DEBUG else logging.INFO
    setup_logger(level=log_level_value, logs_dir=logs_dir)
    logger = get_logger()
    config_name_display = config.__class__.__name__
    logger.info(f'正在启动应用... (环境: {config_name_display})')
    
    # 初始化数据库
    try:
        init_database()
        logger.info('数据库初始化完成')
        
        # 初始化频道模板表
        from app.models.channel_template import init_channel_template_table, seed_channel_templates
        init_channel_template_table()
        seed_channel_templates()
        logger.info('频道模板表初始化完成')
        
        from app.services import LogService
        LogService.log('system', 'app_start', '应用启动完成', level='info')
    except Exception as e:
        logger.error(f'数据库初始化失败: {e}')
        raise
    
    # 初始化定时任务调度器
    try:
        init_scheduler()
        logger.info('定时任务调度器初始化成功')
        
        # 从数据库同步任务到调度器
        ScheduleService.sync_tasks_to_scheduler()
        
        # 注册任务执行回调
        _register_task_callbacks()
        logger.info('任务回调已注册')
        
        # 初始化日志清理任务（每天凌晨2点执行）
        _init_log_cleanup_task()
        logger.info('日志清理任务已初始化')
    except Exception as e:
        logger.error(f'初始化定时任务调度器失败: {e}')
    
    # 注册蓝图（路由）- 必须在静态文件路由之前！
    register_blueprints(app)
    
    # 静态文件和首页路由 - 在最后，作为备选路由
    @app.route('/')
    def index():
        # 获取 public 文件夹的路径
        public_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'public')
        return send_from_directory(public_dir, 'index.html')
    
    # 提供静态文件 - 不拦截 /api 路由
    @app.route('/<path:filename>')
    def static_files(filename):
        # 不处理 API 路由
        if filename.startswith('api/') or filename.startswith('api'):
            return {'error': '资源不存在'}, 404
            
        public_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'public')
        try:
            return send_from_directory(public_dir, filename)
        except Exception as e:
            # 如果文件不存在，返回 404
            logger.warning(f'静态文件不存在: {filename}, 错误: {e}')
            return {'error': '资源不存在'}, 404
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        return {'error': '资源不存在'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f'内部错误: {error}')
        return {'error': '服务器内部错误'}, 500
    
    logger.info('应用启动完成')
    
    return app


def _register_task_callbacks():
    """注册任务执行回调"""
    from app.services.iptv_service import IPTVService
    from app.services import LogService, ScheduleService
    
    scheduler = get_scheduler()
    logger = get_logger('task_executor')
    
    def fetch_channels_callback(task):
        """获取直播源回调"""
        try:
            LogService.log_task(task.task_id, task.account_id, task.task_type, 'running', '任务开始执行')
            result = IPTVService.fetch_and_save_channels(
                account_id=task.account_id,
                filter_sd=task.filter_sd,
                channel_filters=task.channel_filters
            )
            logger.info(f'任务 {task.task_id} 执行结果: {result}')
            ScheduleService.record_execution(task.task_id, result.get('success', False), result.get('message'))
            status = 'success' if result.get('success') else 'failed'
            LogService.log_task(task.task_id, task.account_id, task.task_type, status, result.get('message', ''))
        except Exception as e:
            logger.error(f'任务 {task.task_id} 执行失败: {e}')
            ScheduleService.record_execution(task.task_id, False, str(e))
            LogService.log_task(task.task_id, task.account_id, task.task_type, 'failed', str(e))
    
    # 注册回调
    scheduler.register_callback('fetch_channels', fetch_channels_callback)


def _init_log_cleanup_task():
    """初始化日志清理定时任务（每天凌晨2点执行，清理超过15天的日志）"""
    from app.services import LogService
    import threading
    from datetime import datetime, timedelta
    
    logger = get_logger('log_cleaner')
    
    def cleanup_logs():
        """清理日志的回调函数"""
        try:
            LogService.cleanup_old_logs(days=15)
            logger.info('日志清理任务执行成功')
        except Exception as e:
            logger.error(f'日志清理任务执行失败: {e}')
    
    def run_cleanup_scheduler():
        """后台线程：每天凌晨2点执行日志清理"""
        while True:
            now = datetime.now()
            # 计算下次执行时间（凌晨2点）
            tomorrow_2am = now.replace(hour=2, minute=0, second=0, microsecond=0)
            if now >= tomorrow_2am:
                # 如果已过凌晨2点，则安排明天凌晨2点
                tomorrow_2am += timedelta(days=1)
            
            # 计算睡眠时间
            sleep_seconds = (tomorrow_2am - now).total_seconds()
            logger.info(f'日志清理任务将在 {sleep_seconds / 3600:.1f} 小时后执行（{tomorrow_2am.strftime("%Y-%m-%d %H:%M:%S")}）')
            
            # 等待直到凌晨2点
            import time
            time.sleep(max(1, sleep_seconds))
            
            # 执行清理
            cleanup_logs()
    
    # 启动后台线程进行日志清理
    cleanup_thread = threading.Thread(target=run_cleanup_scheduler, daemon=True)
    cleanup_thread.name = 'LogCleanupThread'
    cleanup_thread.start()
    logger.info('日志清理后台线程已启动（每天凌晨2点执行）')



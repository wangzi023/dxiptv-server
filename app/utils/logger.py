"""
日志工具 - 应用日志管理
"""
import logging
import logging.handlers
import os
from datetime import datetime


logger = logging.getLogger('iptv-system')


def setup_logger(name=None, level=logging.INFO, logs_dir=None):
    """
    配置日志系统
    
    Args:
        name (str): 日志名称
        level: 日志级别
        logs_dir (str): 日志目录
        
    Returns:
        logging.Logger: 日志对象
    """
    if name is None:
        name = 'iptv-system'
    
    if logs_dir is None:
        # 默认日志目录
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    
    # 确保日志目录存在
    os.makedirs(logs_dir, exist_ok=True)
    
    log = logging.getLogger(name)
    log.setLevel(level)
    
    # 清除已有的处理器（避免重复）
    log.handlers = []
    
    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    log.addHandler(console_handler)
    
    # 文件处理器（日志轮转）
    log_file = os.path.join(logs_dir, 'iptv-system.log')
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10485760,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)
    
    return log


def get_logger(name=None):
    """
    获取日志对象
    
    Args:
        name (str): 日志名称
        
    Returns:
        logging.Logger: 日志对象
    """
    if name is None:
        return logger
    return logging.getLogger(name)


# 初始化日志（使用默认配置）
# 注意：此处仅初始化基本日志，完整配置在应用工厂中进行
setup_logger(level=logging.INFO)

"""
数据库工具 - 连接管理和初始化
"""
import sqlite3
import os
from contextlib import contextmanager
from config import get_config


config = get_config()


def get_db_connection():
    """
    获取数据库连接
    
    Returns:
        sqlite3.Connection: 数据库连接对象
    """
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db_context():
    """
    数据库上下文管理器
    
    使用方法:
        with get_db_context() as db:
            db.execute('SELECT * FROM users')
    """
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()


def execute_query(sql, params=None, fetch_one=False):
    """
    执行数据库查询
    
    Args:
        sql (str): SQL 语句
        params (tuple): 参数
        fetch_one (bool): 是否只返回一行
        
    Returns:
        dict 或 list: 查询结果
    """
    with get_db_context() as db:
        cursor = db.execute(sql, params or ())
        if fetch_one:
            row = cursor.fetchone()
            return dict(row) if row else None
        return [dict(row) for row in cursor.fetchall()]


def execute_update(sql, params=None):
    """
    执行数据库更新操作
    
    Args:
        sql (str): SQL 语句
        params (tuple): 参数
        
    Returns:
        int: 受影响的行数
    """
    with get_db_context() as db:
        cursor = db.execute(sql, params or ())
        db.commit()
        return cursor.rowcount


def table_exists(table_name):
    """
    检查表是否存在
    
    Args:
        table_name (str): 表名
        
    Returns:
        bool: 是否存在
    """
    result = execute_query(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
        fetch_one=True
    )
    return result is not None

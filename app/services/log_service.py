"""
日志服务 - 统一处理日志写入与查询
"""
import json
from typing import Optional, Dict, Any
from app.utils import execute_query, execute_update, get_logger

logger = get_logger('log_service')


class LogService:
    """集中处理日志入库与查询"""

    @staticmethod
    def log(
        log_type: str,
        action: str,
        message: str,
        level: str = 'info',
        status: Optional[str] = None,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> int:
        """写入一条日志"""
        extra_text = json.dumps(extra, ensure_ascii=False) if extra else None
        sql = (
            """
            INSERT INTO logs (
                log_type, action, level, message, status,
                user_id, username, target_type, target_id, extra, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """
        )
        execute_update(
            sql,
            (
                log_type,
                action,
                level,
                message,
                status,
                user_id,
                username,
                target_type,
                target_id,
                extra_text,
            ),
        )
        # SQLite rowid can be fetched with last_insert_rowid(); here we just return 0
        # to keep interface simple; caller seldom needs it.
        return 0

    @staticmethod
    def query_logs(
        log_type: Optional[str] = None,
        level: Optional[str] = None,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """按条件分页查询日志"""
        page = max(1, int(page or 1))
        page_size = max(1, min(int(page_size or 20), 100))
        where_clauses = []
        params = []

        if log_type:
            where_clauses.append("log_type = ?")
            params.append(log_type)
        if level:
            where_clauses.append("level = ?")
            params.append(level)
        if status:
            where_clauses.append("status = ?")
            params.append(status)
        if keyword:
            where_clauses.append("(message LIKE ? OR action LIKE ?)" )
            like_kw = f"%{keyword}%"
            params.extend([like_kw, like_kw])

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ''

        total_row = execute_query(
            f"SELECT COUNT(*) as count FROM logs {where_sql}", tuple(params), fetch_one=True
        )
        total = total_row['count'] if total_row else 0

        offset = (page - 1) * page_size
        data_sql = (
            f"""
            SELECT id, log_type, action, level, message, status, user_id, username,
                   target_type, target_id, extra, created_at
            FROM logs
            {where_sql}
            ORDER BY created_at DESC, id DESC
            LIMIT ? OFFSET ?
            """
        )
        data = execute_query(data_sql, tuple(params + [page_size, offset]))

        return {
            'items': data,
            'total': total,
            'page': page,
            'page_size': page_size,
        }

    @staticmethod
    def log_task(task_id: int, account_id: int, task_type: str, status: str, message: str):
        """任务执行日志"""
        LogService.log(
            log_type='task',
            action=task_type,
            message=message,
            level='info' if status == 'success' else 'warning' if status == 'running' else 'error',
            status=status,
            target_type='schedule_task',
            target_id=task_id,
            extra={'account_id': account_id, 'task_type': task_type},
        )

    @staticmethod
    def log_operation(action: str, message: str, user_id: int, username: str, status: Optional[str] = None):
        LogService.log(
            log_type='operation',
            action=action,
            message=message,
            level='info',
            status=status,
            user_id=user_id,
            username=username,
        )

    @staticmethod
    def log_auth(action: str, message: str, user_id: Optional[int], username: Optional[str]):
        LogService.log(
            log_type='auth',
            action=action,
            message=message,
            level='info',
            user_id=user_id,
            username=username,
        )

    @staticmethod
    def cleanup_old_logs(days: int = 15) -> int:
        """清除超过指定天数的日志（默认15天）"""
        sql = "DELETE FROM logs WHERE created_at < datetime('now', '-' || ? || ' days')"
        result = execute_update(sql, (days,))
        logger.info(f'日志清理完成：删除超过{days}天的日志记录')
        return result
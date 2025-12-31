"""
数据库初始化和管理
"""
from app.utils import get_db_context, execute_update
from app.utils.auth import hash_password
from config import get_config


config = get_config()


def init_database():
    """初始化数据库"""
    with get_db_context() as db:
        cursor = db.cursor()
        
        # 创建用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'admin',
                is_first_login INTEGER DEFAULT 1,
                is_default INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建默认管理员
        cursor.execute('SELECT COUNT(*) as count FROM users WHERE username = ?', 
                      (config.DEFAULT_ADMIN_USERNAME,))
        if cursor.fetchone()['count'] == 0:
            default_password_hash = hash_password(config.DEFAULT_ADMIN_PASSWORD)
            cursor.execute('''
                INSERT INTO users (username, password, role, is_first_login, is_default, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (config.DEFAULT_ADMIN_USERNAME, default_password_hash, 'admin', 1, 1, 1))
        
        # 创建账户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                mac TEXT NOT NULL,
                imei TEXT,
                address TEXT,
                remark TEXT,
                source_id INTEGER,
                last_fetch_time DATETIME,
                last_fetch_status TEXT,
                status INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE SET NULL
            )
        ''')
        
        # 创建源表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                account_id INTEGER,
                channel_count INTEGER DEFAULT 0,
                last_updated DATETIME,
                status INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
            )
        ''')
        
        # 创建频道表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT NOT NULL,
                channel_name TEXT NOT NULL,
                channel_url TEXT NOT NULL,
                user_channel_id TEXT,
                time_shift TEXT,
                channel_sdp_url TEXT,
                channel_logo_url TEXT,
                positon TEXT,
                source_id INTEGER,
                category TEXT,
                status INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE
            )
        ''')
        
        # 创建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_channels_source 
            ON channels(source_id)
        ''')
        
        # 创建定时任务表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedule_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                task_type TEXT NOT NULL,
                schedule_time TEXT NOT NULL,
                repeat_type TEXT DEFAULT 'daily',
                filter_sd INTEGER DEFAULT 1,
                channel_filters TEXT,
                is_enabled INTEGER DEFAULT 1,
                last_executed DATETIME,
                next_execution DATETIME,
                execution_count INTEGER DEFAULT 0,
                last_error TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
            )
        ''')
        
        # 创建定时任务索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_schedule_tasks_account 
            ON schedule_tasks(account_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_schedule_tasks_enabled 
            ON schedule_tasks(is_enabled)
        ''')

        # 创建日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_type TEXT NOT NULL,
                action TEXT,
                level TEXT DEFAULT 'info',
                message TEXT,
                status TEXT,
                user_id INTEGER,
                username TEXT,
                target_type TEXT,
                target_id INTEGER,
                extra TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_logs_type_created
            ON logs(log_type, created_at)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_logs_level
            ON logs(level)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_logs_status
            ON logs(status)
        ''')
        
        # 数据库迁移：为accounts表添加remark字段（如果不存在）
        try:
            cursor.execute("SELECT remark FROM accounts LIMIT 1")
        except Exception:
            cursor.execute("ALTER TABLE accounts ADD COLUMN remark TEXT")
            db.commit()

        # 数据库迁移：将status字段统一为数字（0 启用, 1 停用）
        try:
            cursor.execute("UPDATE accounts SET status = 0 WHERE status IN ('active', '启用', '0', 0) OR status IS NULL")
            cursor.execute("UPDATE accounts SET status = 1 WHERE status IN ('inactive', '停用', '1', 1)")
            cursor.execute("UPDATE sources SET status = 0 WHERE status IN ('active', '启用', '0', 0) OR status IS NULL")
            cursor.execute("UPDATE sources SET status = 1 WHERE status IN ('inactive', '停用', '1', 1)")
            cursor.execute("""
                UPDATE channels
                SET status = CASE
                    WHEN status IN ('active', '启用', 1, '1') OR status IS NULL THEN 0
                    WHEN status IN ('inactive', '停用', 0, '0') THEN 1
                    ELSE status
                END
            """)
            db.commit()
        except Exception:
            pass
        
        db.commit()

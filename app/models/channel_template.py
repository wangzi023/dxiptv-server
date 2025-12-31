"""
频道模板数据库模型
"""
from app.utils import get_db_context, execute_update


def init_channel_template_table():
    """初始化频道模板表"""
    with get_db_context() as db:
        cursor = db.cursor()
        
        # 创建频道模板表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channel_template (
                id INTEGER PRIMARY KEY,
                channel_id TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                group_title TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_channel_template_channel_id 
            ON channel_template(channel_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_channel_template_group 
            ON channel_template(group_title)
        ''')
        
        db.commit()


def seed_channel_templates():
    """从 data.json 导入初始频道模板数据"""
    import json
    import os
    from config import get_config
    
    config = get_config()
    data_json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'public', 'data.json')
    
    # 检查文件是否存在
    if not os.path.exists(data_json_path):
        print(f"警告: data.json 文件不存在: {data_json_path}")
        return
    
    # 读取 JSON 文件
    with open(data_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    channels = data.get('channels', [])
    if not channels:
        print("警告: data.json 中没有频道数据")
        return
    
    # 批量插入数据
    with get_db_context() as db:
        cursor = db.cursor()
        
        # 检查是否已经有数据
        cursor.execute('SELECT COUNT(*) as count FROM channel_template')
        count = cursor.fetchone()['count']
        
        if count > 0:
            print(f"频道模板表已有 {count} 条数据，跳过初始化")
            return
        
        # 插入数据
        inserted = 0
        for channel in channels:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO channel_template (id, channel_id, name, group_title)
                    VALUES (?, ?, ?, ?)
                ''', (
                    channel['id'],
                    channel['channel_id'],
                    channel['name'],
                    channel['group_title']
                ))
                if cursor.rowcount > 0:
                    inserted += 1
            except Exception as e:
                print(f"插入频道模板失败: {channel}, 错误: {e}")
        
        db.commit()
        print(f"成功导入 {inserted} 条频道模板数据")

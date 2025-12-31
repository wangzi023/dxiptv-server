"""
频道模板服务
"""
from app.utils import get_db_context, execute_query, execute_update
from app.utils.logger import get_logger
from datetime import datetime

logger = get_logger()


class ChannelTemplateService:
    """频道模板服务"""
    
    @staticmethod
    def get_all_templates(group_title=None):
        """
        获取所有频道模板
        
        Args:
            group_title (str): 可选，按分组筛选
            
        Returns:
            list: 频道模板列表
        """
        try:
            if group_title:
                return execute_query(
                    'SELECT * FROM channel_template WHERE group_title = ? ORDER BY id',
                    (group_title,),
                    fetch_one=False
                )
            else:
                return execute_query(
                    'SELECT * FROM channel_template ORDER BY id',
                    fetch_one=False
                )
        except Exception as e:
            logger.error(f"获取频道模板失败: {e}")
            return []
    
    @staticmethod
    def get_template_by_channel_id(channel_id):
        """
        根据 channel_id 获取模板
        
        Args:
            channel_id (str): 频道ID
            
        Returns:
            dict: 频道模板信息
        """
        try:
            return execute_query(
                'SELECT * FROM channel_template WHERE channel_id = ?',
                (str(channel_id),),
                fetch_one=True
            )
        except Exception as e:
            logger.error(f"查询频道模板失败: {e}")
            return None
    
    @staticmethod
    def get_template_by_id(template_id):
        """
        根据 ID 获取模板
        
        Args:
            template_id (int): 模板ID
            
        Returns:
            dict: 频道模板信息
        """
        try:
            return execute_query(
                'SELECT * FROM channel_template WHERE id = ?',
                (template_id,),
                fetch_one=True
            )
        except Exception as e:
            logger.error(f"查询频道模板失败: {e}")
            return None
    
    @staticmethod
    def get_all_groups():
        """
        获取所有分组
        
        Returns:
            list: 分组列表
        """
        try:
            result = execute_query(
                'SELECT DISTINCT group_title FROM channel_template ORDER BY group_title',
                fetch_one=False
            )
            return [row['group_title'] for row in result]
        except Exception as e:
            logger.error(f"获取分组列表失败: {e}")
            return []
    
    @staticmethod
    def get_statistics():
        """
        获取模板统计信息
        
        Returns:
            dict: 统计信息
        """
        try:
            total = execute_query(
                'SELECT COUNT(*) as count FROM channel_template',
                fetch_one=True
            )['count']
            
            groups = execute_query(
                '''SELECT group_title, COUNT(*) as count 
                   FROM channel_template 
                   GROUP BY group_title 
                   ORDER BY count DESC''',
                fetch_one=False
            )
            
            return {
                'total': total,
                'groups': {g['group_title']: g['count'] for g in groups}
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {'total': 0, 'groups': {}}
    
    @staticmethod
    def add_template(channel_id, name, group_title):
        """
        添加频道模板
        
        Args:
            channel_id (str): 频道ID
            name (str): 频道名称
            group_title (str): 分组名称
            
        Returns:
            dict: 操作结果
        """
        try:
            # 检查 channel_id 是否已存在
            existing = execute_query(
                'SELECT id FROM channel_template WHERE channel_id = ?',
                (str(channel_id),),
                fetch_one=True
            )
            
            if existing:
                return {'success': False, 'message': f'频道ID {channel_id} 已存在'}
            
            # 获取最大ID
            max_id = execute_query(
                'SELECT MAX(id) as max_id FROM channel_template',
                fetch_one=True
            )['max_id']
            
            new_id = (max_id or 0) + 1
            
            # 插入新模板
            execute_update(
                '''INSERT INTO channel_template (id, channel_id, name, group_title)
                   VALUES (?, ?, ?, ?)''',
                (new_id, str(channel_id), name, group_title)
            )
            
            logger.info(f"添加频道模板: {name} ({channel_id}) - {group_title}")
            return {'success': True, 'message': '添加成功', 'id': new_id}
            
        except Exception as e:
            logger.error(f"添加频道模板失败: {e}")
            return {'success': False, 'message': str(e)}
    
    @staticmethod
    def update_template(template_id, channel_id=None, name=None, group_title=None):
        """
        更新频道模板
        
        Args:
            template_id (int): 模板ID
            channel_id (str): 频道ID（可选）
            name (str): 频道名称（可选）
            group_title (str): 分组名称（可选）
            
        Returns:
            dict: 操作结果
        """
        try:
            # 检查模板是否存在
            template = execute_query(
                'SELECT * FROM channel_template WHERE id = ?',
                (template_id,),
                fetch_one=True
            )
            
            if not template:
                return {'success': False, 'message': f'模板ID {template_id} 不存在'}
            
            # 如果要更新 channel_id，检查是否与其他记录冲突
            if channel_id and channel_id != template['channel_id']:
                existing = execute_query(
                    'SELECT id FROM channel_template WHERE channel_id = ? AND id != ?',
                    (str(channel_id), template_id),
                    fetch_one=True
                )
                if existing:
                    return {'success': False, 'message': f'频道ID {channel_id} 已被其他模板使用'}
            
            # 构建更新语句
            updates = []
            params = []
            
            if channel_id is not None:
                updates.append('channel_id = ?')
                params.append(str(channel_id))
            
            if name is not None:
                updates.append('name = ?')
                params.append(name)
            
            if group_title is not None:
                updates.append('group_title = ?')
                params.append(group_title)
            
            if not updates:
                return {'success': False, 'message': '没有要更新的字段'}
            
            updates.append('updated_at = ?')
            params.append(datetime.now().isoformat())
            params.append(template_id)
            
            sql = f"UPDATE channel_template SET {', '.join(updates)} WHERE id = ?"
            execute_update(sql, tuple(params))
            
            logger.info(f"更新频道模板: ID={template_id}")
            return {'success': True, 'message': '更新成功'}
            
        except Exception as e:
            logger.error(f"更新频道模板失败: {e}")
            return {'success': False, 'message': str(e)}
    
    @staticmethod
    def delete_template(template_id):
        """
        删除频道模板
        
        Args:
            template_id (int): 模板ID
            
        Returns:
            dict: 操作结果
        """
        try:
            # 检查模板是否存在
            template = execute_query(
                'SELECT * FROM channel_template WHERE id = ?',
                (template_id,),
                fetch_one=True
            )
            
            if not template:
                return {'success': False, 'message': f'模板ID {template_id} 不存在'}
            
            # 删除模板
            execute_update(
                'DELETE FROM channel_template WHERE id = ?',
                (template_id,)
            )
            
            logger.info(f"删除频道模板: {template['name']} ({template['channel_id']})")
            return {'success': True, 'message': '删除成功'}
            
        except Exception as e:
            logger.error(f"删除频道模板失败: {e}")
            return {'success': False, 'message': str(e)}
    
    @staticmethod
    def match_channel_info(channel_id):
        """
        根据 channel_id 匹配频道信息
        如果匹配到模板，返回模板的 name 和 group_title
        如果未匹配，返回 None 和 "未分类"
        
        Args:
            channel_id (str): 频道ID
            
        Returns:
            dict: {'name': 频道名称, 'group_title': 分组}
        """
        template = ChannelTemplateService.get_template_by_channel_id(channel_id)
        
        if template:
            return {
                'name': template['name'],
                'group_title': template['group_title']
            }
        else:
            return {
                'name': None,  # 使用原始名称
                'group_title': '未分类'
            }

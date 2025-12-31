"""
频道匹配服务
将电信接口返回的频道与模板库进行匹配，补充分类等信息
"""

import json
import os
from app.utils import get_logger, execute_query, execute_update

logger = get_logger('channel_matcher')


class ChannelMatcher:
    """频道匹配器"""
    
    def __init__(self):
        self.template_data = None
        self.channel_map = {}  # channel_id -> template
        self._load_template()
    
    def _load_template(self):
        """加载频道模板库"""
        try:
            template_path = os.path.join(
                os.path.dirname(__file__), 
                '../../public/data.json'
            )
            
            if not os.path.exists(template_path):
                logger.warning('频道模板文件不存在')
                return
            
            with open(template_path, 'r', encoding='utf-8') as f:
                self.template_data = json.load(f)
            
            # 建立 channel_id 映射
            for channel in self.template_data.get('channels', []):
                self.channel_map[channel['channel_id']] = channel
            
            logger.info(f'加载了 {len(self.channel_map)} 个模板频道')
            
        except Exception as e:
            logger.error(f'加载频道模板失败: {e}')
    
    def match_channel(self, channel_id):
        """
        根据 channel_id 匹配模板频道
        
        Args:
            channel_id: 电信接口返回的频道ID
            
        Returns:
            dict: 匹配到的模板频道信息，包含 name, group_title 等
            None: 未匹配到
        """
        return self.channel_map.get(str(channel_id))
    
    def enrich_channel(self, channel_data):
        """
        增强频道数据，补充分类等信息
        
        Args:
            channel_data: 电信接口返回的频道数据
                {
                    'ChannelID': '6197',
                    'ChannelName': '广东卫视高清',
                    'ChannelURL': 'igmp://...',
                    ...
                }
        
        Returns:
            dict: 增强后的频道数据
                {
                    'channel_id': '6197',
                    'channel_name': '广东卫视',  # 使用模板名称
                    'channel_url': 'igmp://...',
                    'category': '广东',  # 从模板补充
                    'template_name': '广东卫视',  # 模板标准名称
                    'is_matched': True
                }
        """
        channel_id = channel_data.get('ChannelID', '')
        channel_name = channel_data.get('ChannelName', '')
        channel_url = channel_data.get('ChannelURL', '')
        
        # 匹配模板
        template = self.match_channel(channel_id)
        
        enriched = {
            'channel_id': channel_id,
            'channel_name': channel_name,
            'channel_url': channel_url,
            'user_channel_id': channel_data.get('UserChannelID', ''),
            'time_shift': channel_data.get('TimeShift', ''),
            'channel_sdp_url': channel_data.get('ChannelSDP', ''),
            'channel_logo_url': channel_data.get('ChannelLogoURL', ''),
            'positon': channel_data.get('Postion', ''),
            'is_matched': False,
            'category': None,
            'template_name': None
        }
        
        if template:
            enriched['is_matched'] = True
            enriched['category'] = template.get('group_title')
            enriched['template_name'] = template.get('name')
            # 优先使用模板的标准名称
            enriched['channel_name'] = template.get('name')
            
            logger.debug(f'频道 {channel_id} 匹配成功: {enriched["template_name"]} ({enriched["category"]})')
        else:
            logger.debug(f'频道 {channel_id} 未匹配到模板: {channel_name}')
        
        return enriched
    
    def enrich_channels_batch(self, channels_data):
        """
        批量增强频道数据
        
        Args:
            channels_data: 电信接口返回的频道列表
        
        Returns:
            list: 增强后的频道列表
        """
        enriched_channels = []
        matched_count = 0
        
        for channel in channels_data:
            enriched = self.enrich_channel(channel)
            enriched_channels.append(enriched)
            
            if enriched['is_matched']:
                matched_count += 1
        
        logger.info(f'批量增强完成: 总数 {len(channels_data)}, 匹配 {matched_count}, 未匹配 {len(channels_data) - matched_count}')
        
        return enriched_channels
    
    def update_database_categories(self, source_id):
        """
        更新数据库中已存在频道的分类信息
        
        Args:
            source_id: 源ID
            
        Returns:
            dict: 更新结果 {'updated': 10, 'skipped': 5}
        """
        try:
            # 获取该源下的所有频道
            sql = """
                SELECT id, channel_id, channel_name, category
                FROM channels
                WHERE source_id = ?
            """
            channels = execute_query(sql, (source_id,))
            
            updated_count = 0
            skipped_count = 0
            
            for channel in channels:
                # 匹配模板
                template = self.match_channel(channel['channel_id'])
                
                if template:
                    new_category = template.get('group_title')
                    new_name = template.get('name')
                    
                    # 更新分类和标准名称
                    if channel['category'] != new_category:
                        update_sql = """
                            UPDATE channels 
                            SET category = ?, channel_name = ?, updated_at = datetime('now')
                            WHERE id = ?
                        """
                        execute_update(update_sql, (new_category, new_name, channel['id']))
                        updated_count += 1
                        logger.debug(f'更新频道 {channel["id"]}: {new_name} -> {new_category}')
                    else:
                        skipped_count += 1
                else:
                    skipped_count += 1
            
            logger.info(f'分类更新完成: 更新 {updated_count}, 跳过 {skipped_count}')
            
            return {
                'updated': updated_count,
                'skipped': skipped_count
            }
            
        except Exception as e:
            logger.error(f'更新数据库分类失败: {e}')
            raise
    
    def get_statistics(self):
        """
        获取模板库统计信息
        
        Returns:
            dict: 统计信息
        """
        if not self.template_data:
            return None
        
        categories = {}
        for channel in self.template_data.get('channels', []):
            category = channel.get('group_title', '未分类')
            categories[category] = categories.get(category, 0) + 1
        
        return {
            'total': len(self.channel_map),
            'categories': categories
        }


# 全局实例
_matcher_instance = None


def get_channel_matcher():
    """获取频道匹配器单例"""
    global _matcher_instance
    if _matcher_instance is None:
        _matcher_instance = ChannelMatcher()
    return _matcher_instance

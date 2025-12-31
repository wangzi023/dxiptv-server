"""
IPTV 直播源服务层
负责调用 tellyget_core 获取频道并保存到数据库
"""

from datetime import datetime
from app.utils.tellyget_core import TellyGetCore
from app.utils.database import execute_query, execute_update
from app.utils import get_logger
from app.services.channel_template_service import ChannelTemplateService

logger = get_logger('iptv_service')


class IPTVService:
    """IPTV 服务类"""
    
    @staticmethod
    def fetch_and_save_channels(account_id, filter_sd=True, channel_filters=None):
        """
        获取并保存频道到数据库
        
        Args:
            account_id: 账户 ID（从 accounts 表）
            filter_sd: 是否过滤标清频道
            channel_filters: 频道名称过滤器
            
        Returns:
            dict: {
                'success': bool,
                'message': str,
                'channel_count': int
            }
        """
        try:
            # 获取账户信息
            account = IPTVService._get_account(account_id)
            if not account:
                return {
                    'success': False,
                    'message': '账户不存在',
                    'channel_count': 0
                }
            
            # 检查账户是否有关联的直播源
            if not account['source_id']:
                logger.warning(f'账户 {account["username"]} (ID: {account_id}) 没有关联直播源')
                return {
                    'success': False,
                    'message': '账户未关联直播源，请先获取直播源',
                    'channel_count': 0
                }
            
            logger.info(f'开始获取账户 {account["username"]} 的频道')
            
            # 创建 TellyGet 实例
            core = TellyGetCore(
                user=account['username'].replace('@iptv.gd', ''),  # 去掉后缀
                passwd=account['password'],
                mac=account['mac'],
                imei=account.get('imei', ''),
                address=account.get('address', '')
            )
            
            # 获取频道
            success, result = core.fetch_channels(filter_sd, channel_filters)
            
            if not success:
                return {
                    'success': False,
                    'message': f'获取频道失败: {result}',
                    'channel_count': 0
                }
            
            channels = result
            logger.info(f'获取到 {len(channels)} 个频道，开始保存到数据库')
            
            # 保存到数据库
            saved_count = IPTVService._save_channels_to_db(account_id, channels)
            
            # 更新账户状态
            IPTVService._update_account_status(account_id, success=True)
            
            return {
                'success': True,
                'message': f'成功保存 {saved_count} 个频道',
                'channel_count': saved_count
            }
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            error_msg = str(e) if str(e) else f"{type(e).__name__}: 无详细信息"
            logger.error(f'获取并保存频道异常: {error_msg}\n{error_trace}')
            IPTVService._update_account_status(account_id, success=False, error=error_msg)
            return {
                'success': False,
                'message': f'系统异常: {error_msg}',
                'channel_count': 0
            }

    @staticmethod
    def _get_account(account_id):
        """获取账户信息"""
        sql = """
            SELECT id, username, password, mac, imei, address, source_id
            FROM accounts
            WHERE id = ?
        """
        result = execute_query(sql, (account_id,))
        if result and len(result) > 0:
            row = result[0]
            return {
                'id': row['id'],
                'username': row['username'],
                'password': row['password'],
                'mac': row['mac'],
                'imei': row['imei'] or '',
                'address': row['address'] or '',
                'source_id': row['source_id']
            }
        return None

    @staticmethod
    def _save_channels_to_db(account_id, channels):
        """保存频道到数据库（自动匹配模板库补充分类信息）"""
        account = IPTVService._get_account(account_id)
        if not account or not account['source_id']:
            logger.warning(f'账户 {account_id} 没有关联直播源')
            return 0
        
        source_id = account['source_id']
        saved_count = 0
        matched_count = 0
        
        for channel in channels:
            try:
                # 解析频道信息
                parsed = TellyGetCore.parse_channel_info(channel)
                
                # 使用模板匹配频道名称和分组
                channel_id = parsed['channel_id']
                match_info = ChannelTemplateService.match_channel_info(channel_id)
                
                # 使用匹配结果或原始信息
                final_name = match_info['name'] if match_info['name'] else parsed['channel_name']
                final_category = match_info['group_title']  # "未分类" 或实际分类
                
                # 统计匹配成功的频道
                if match_info['name']:
                    matched_count += 1
                
                # 检查频道是否已存在
                check_sql = """
                    SELECT id FROM channels
                    WHERE source_id = ? AND channel_id = ?
                """
                existing = execute_query(check_sql, (source_id, channel_id))
                
                if existing:
                    # 更新已存在的频道（包含分类信息）
                    update_sql = """
                        UPDATE channels
                        SET channel_name = ?,
                            channel_url = ?,
                            channel_logo_url = ?,
                            category = ?,
                            updated_at = ?
                        WHERE source_id = ? AND channel_id = ?
                    """
                    execute_update(update_sql, (
                        final_name,
                        parsed['channel_url'],
                        parsed['channel_logo_url'],
                        final_category,
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        source_id,
                        channel_id
                    ))
                else:
                    # 插入新频道（包含分类信息）
                    insert_sql = """
                        INSERT INTO channels (
                            source_id, channel_id, channel_name, channel_url,
                            user_channel_id, time_shift, channel_sdp_url,
                            channel_logo_url, positon, category, status,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    execute_update(insert_sql, (
                        source_id,
                        channel_id,
                        final_name,
                        parsed['channel_url'],
                        parsed['user_channel_id'],
                        parsed['time_shift'],
                        parsed['channel_sdp_url'],
                        parsed['channel_logo_url'],
                        parsed['positon'],
                        final_category,
                        0,  # status: 0 表示启用
                        now,
                        now
                    ))
                
                saved_count += 1
                
            except Exception as e:
                logger.error(f'保存频道失败 {parsed.get("channel_name", "Unknown")}: {e}')
                continue
        
        logger.info(f'成功保存 {saved_count} 个频道，其中 {matched_count} 个匹配到模板库')
        return saved_count

    @staticmethod
    def _update_account_status(account_id, success=True, error=None):
        """更新账户状态"""
        sql = """
            UPDATE accounts
            SET last_fetch_time = ?,
                last_fetch_status = ?
            WHERE id = ?
        """
        status = 'success' if success else 'failed'
        execute_update(sql, (
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            status if not error else f'{status}: {error}',
            account_id
        ))

    @staticmethod
    def get_channels_by_source(source_id, status=None):
        """
        获取直播源的所有频道
        
        Args:
            source_id: 直播源 ID
            status: 频道状态（可选）
            
        Returns:
            list: 频道列表
        """
        if status is not None:
            sql = """
                SELECT id, channel_id, channel_name, channel_url,
                       channel_logo_url, status, created_at, updated_at
                FROM channels
                WHERE source_id = ? AND status = ?
                ORDER BY positon ASC, id ASC
            """
            result = execute_query(sql, (source_id, status))
        else:
            sql = """
                SELECT id, channel_id, channel_name, channel_url,
                       channel_logo_url, status, created_at, updated_at
                FROM channels
                WHERE source_id = ?
                ORDER BY positon ASC, id ASC
            """
            result = execute_query(sql, (source_id,))
        
        channels = []
        for row in result:
            channels.append({
                'id': row[0],
                'channel_id': row[1],
                'channel_name': row[2],
                'channel_url': row[3],
                'channel_logo_url': row[4],
                'status': row[5],
                'created_at': row[6],
                'updated_at': row[7]
            })
        
        return channels

    @staticmethod
    def update_channel_status(channel_id, status):
        """
        更新频道状态
        
        Args:
            channel_id: 频道 ID
            status: 状态（0: 启用, 1: 禁用）
            
        Returns:
            bool: 是否成功
        """
        sql = """
            UPDATE channels
            SET status = ?,
                updated_at = ?
            WHERE id = ?
        """
        try:
            execute_update(sql, (
                status,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                channel_id
            ))
            return True
        except Exception as e:
            logger.error(f'更新频道状态失败: {e}')
            return False

    @staticmethod
    def delete_channels_by_source(source_id):
        """
        删除直播源的所有频道
        
        Args:
            source_id: 直播源 ID
            
        Returns:
            bool: 是否成功
        """
        sql = "DELETE FROM channels WHERE source_id = ?"
        try:
            execute_update(sql, (source_id,))
            logger.info(f'删除直播源 {source_id} 的所有频道')
            return True
        except Exception as e:
            logger.error(f'删除频道失败: {e}')
            return False

    @staticmethod
    def get_channel_statistics(source_id):
        """
        获取频道统计信息
        
        Args:
            source_id: 直播源 ID
            
        Returns:
            dict: 统计信息
        """
        sql = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 0 THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) as inactive
            FROM channels
            WHERE source_id = ?
        """
        result = execute_query(sql, (source_id,))
        
        if result and len(result) > 0:
            row = result[0]
            return {
                'total': row[0],
                'active': row[1],
                'inactive': row[2]
            }
        
        return {
            'total': 0,
            'active': 0,
            'inactive': 0
        }

"""
电信 IPTV 直播源获取核心模块
基于 tellyget-gd 项目改造，用于获取广东电信 IPTV 直播源并保存到数据库

原项目: https://github.com/fejich/tellyget-gd
License: GNU General Public License v3.0
Modified by: DXIPTV Server Project

主要功能:
1. 认证广东电信 IPTV 账户
2. 获取所有频道列表
3. 解析频道信息（名称、ID、URL）
4. 保存到数据库而不是输出 m3u 文件
"""

import json
import re
import requests
import hashlib
from random import randint
from bs4 import BeautifulSoup
from urllib.parse import urlunparse, urlparse
from Crypto.Cipher import DES3
from Crypto.Util.Padding import pad, unpad

from app.utils import get_logger

logger = get_logger('tellyget_core')


class Cipher:
    """DES3 加密/解密工具"""
    def __init__(self, key):
        self.cipher = DES3.new(key.encode(), DES3.MODE_ECB)

    def encrypt(self, plain_text):
        """加密"""
        cipher_text = self.cipher.encrypt(pad(plain_text.encode(), DES3.block_size))
        return cipher_text.hex().upper()

    def decrypt(self, cipher_text):
        """解密"""
        plain_text = unpad(self.cipher.decrypt(bytes.fromhex(cipher_text)), DES3.block_size)
        return plain_text.decode()


class Authenticator:
    """IPTV 认证器"""
    def __init__(self, passwd):
        key = hashlib.md5(passwd.encode()).hexdigest()[:24].upper()
        self.cipher = Cipher(key)

    def build(self, token, user_id, stb_id, ip, mac):
        """构建认证信息"""
        plain_text = '$'.join([
            str(randint(0, int(1e7))),
            token,
            user_id,
            stb_id,
            ip,
            mac,
            '',
            'CTC'
        ])
        return self.cipher.encrypt(plain_text)


class IPTVAuth:
    """IPTV 认证类"""
    
    DEFAULT_AUTHURL = 'http://eds.iptv.gd.cn:8082/EDS/jsp/AuthenticationURL'
    
    def __init__(self, user, passwd, mac, imei='', address='', authurl=None):
        """
        初始化认证器
        
        Args:
            user: IPTV 账号（去掉 @iptv.gd）
            passwd: IPTV 密码
            mac: 机顶盒 MAC 地址
            imei: IMEI（可选）
            address: IP 地址（可选）
            authurl: 认证 URL（可选）
        """
        self.user = user
        self.passwd = passwd
        self.mac = mac
        self.imei = imei or ''
        self.address = address or ''
        self.authurl = authurl or self.DEFAULT_AUTHURL
        self.session = None
        self.base_url = ''

    def authenticate(self):
        """执行认证流程"""
        try:
            logger.info(f'开始认证 IPTV 账户: {self.user}')
            
            # 创建会话
            self.session = requests.Session()
            self.session.headers = {
                'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.0 (KHTML, like Gecko)',
            }
            
            # 获取 base_url
            self.base_url = self._get_base_url()
            logger.info(f'Base URL: {self.base_url}')
            
            # 登录
            self._login()
            
            logger.info('认证成功')
            return True
            
        except Exception as e:
            logger.error(f'认证失败: {e}')
            return False

    def _get_base_url(self):
        """获取 base URL"""
        params = {
            'UserID': self.user,
            'Action': 'Login'
        }
        response = self.session.get(self.authurl, params=params, allow_redirects=False)
        url = response.headers.get('Location')
        return urlunparse(urlparse(url)._replace(path='', query=''))

    def _get_token(self):
        """获取令牌"""
        params = {
            'response_type': 'EncryToken',
            'client_id': 'smcphone',
            'userid': self.user,
        }
        response = self.session.get(f'{self.base_url}/EPG/oauth/v2/authorize', params=params)
        j = json.loads(response.text)
        return j['EncryToken']

    def _login(self):
        """执行登录"""
        token = self._get_token()
        authenticator = Authenticator(self.passwd).build(
            token, self.user, self.imei, self.address, self.mac
        )
        
        params = {
            'client_id': 'smcphone',
            'DeviceType': 'deviceType',
            'UserID': self.user,
            'DeviceVersion': 'deviceVersion',
            'userdomain': 2,
            'datadomain': 3,
            'accountType': 1,
            'authinfo': authenticator,
            'grant_type': 'EncryToken',
        }
        self.session.get(self.base_url + '/EPG/oauth/v2/token', params=params)


class IPTVChannelFetcher:
    """IPTV 频道获取器"""
    
    def __init__(self, auth):
        """
        初始化
        
        Args:
            auth: IPTVAuth 实例
        """
        self.auth = auth
        self.session = auth.session
        self.base_url = auth.base_url

    def get_channels(self, filter_sd=True, channel_filters=None):
        """
        获取频道列表
        
        Args:
            filter_sd: 是否过滤标清频道（默认 True）
            channel_filters: 频道名称过滤器列表（正则表达式）
            
        Returns:
            list: 频道列表，每个频道包含：
                - ChannelID: 频道 ID
                - ChannelName: 频道名称
                - ChannelURL: 频道 URL
                - ... 其他字段
        """
        try:
            logger.info('开始获取频道列表...')
            
            # 请求频道列表页面
            response = self.session.post(
                self.base_url + '/EPG/jsp/getchannellistHWCTC.jsp'
            )
            
            # 解析 HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            scripts = soup.find_all('script', string=re.compile('ChannelID="[^"]+"'))
            
            logger.info(f'发现 {len(scripts)} 个频道')
            
            channels = []
            filtered_count = 0
            
            # 解析每个频道
            for script in scripts:
                match = re.search(
                    r'Authentication.CTCSetConfig\(\'Channel\',\'(.+?)\'\)',
                    script.string,
                    re.MULTILINE
                )
                
                if not match:
                    continue
                
                channel_params = match.group(1)
                channel = {}
                
                # 解析频道参数
                for channel_param in channel_params.split('",'):
                    if '="' in channel_param:
                        key, value = channel_param.split('="', 1)
                        channel[key] = value
                
                # 应用过滤器
                if channel_filters and self._match_filters(channel, channel_filters):
                    filtered_count += 1
                    continue
                
                channels.append(channel)
            
            logger.info(f'过滤了 {filtered_count} 个频道')
            
            # 过滤标清频道
            if filter_sd:
                removed_count = self._remove_sd_channels(channels)
                logger.info(f'移除了 {removed_count} 个标清候选频道')
            
            logger.info(f'最终获取 {len(channels)} 个频道')
            return channels
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            error_msg = str(e) if str(e) else f"{type(e).__name__}: 无详细信息"
            logger.error(f'获取频道失败: {error_msg}\n{error_trace}')
            raise  # 抛出异常让上层处理

    def _match_filters(self, channel, filters):
        """检查频道是否匹配过滤器"""
        channel_name = channel.get('ChannelName', '')
        for filter_pattern in filters:
            if re.search(filter_pattern, channel_name):
                return True
        return False

    def _remove_sd_channels(self, channels):
        """移除标清频道（如果有对应的高清版本）"""
        original_count = len(channels)
        
        # 找出所有高清频道名
        hd_names = {ch.get('ChannelName', '') for ch in channels if '高清' in ch.get('ChannelName', '')}
        
        # 移除有高清版本的标清频道
        channels[:] = [
            ch for ch in channels
            if not (ch.get('ChannelName', '') + '高清' in hd_names)
        ]
        
        return original_count - len(channels)


class TellyGetCore:
    """
    TellyGet 核心功能封装
    提供简单的接口用于获取 IPTV 频道信息
    """
    
    def __init__(self, user, passwd, mac, **kwargs):
        """
        初始化
        
        Args:
            user: IPTV 账号
            passwd: IPTV 密码
            mac: 机顶盒 MAC 地址
            **kwargs: 其他可选参数（imei, address, authurl）
        """
        self.auth = IPTVAuth(user, passwd, mac, **kwargs)
        self.fetcher = None

    def fetch_channels(self, filter_sd=True, channel_filters=None):
        """
        获取频道列表
        
        Args:
            filter_sd: 是否过滤标清频道
            channel_filters: 频道名称过滤器（正则表达式列表）
            
        Returns:
            tuple: (success, channels)
                - success: 是否成功
                - channels: 频道列表或错误信息
        """
        try:
            # 认证
            if not self.auth.authenticate():
                return False, "认证失败"
            
            # 创建fetcher
            self.fetcher = IPTVChannelFetcher(self.auth)
            
            # 获取频道
            channels = self.fetcher.get_channels(filter_sd, channel_filters)
            
            if not channels:
                return False, "未获取到频道"
            
            return True, channels
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            error_msg = str(e) if str(e) else f"{type(e).__name__}: 无详细信息"
            logger.error(f'获取频道异常: {error_msg}\n{error_trace}')
            return False, error_msg

    @staticmethod
    def parse_channel_info(channel):
        """
        解析频道信息为标准格式
        
        Args:
            channel: 原始频道字典
            
        Returns:
            dict: 标准化的频道信息
        """
        return {
            'channel_id': channel.get('ChannelID', ''),
            'channel_name': channel.get('ChannelName', ''),
            'channel_url': channel.get('ChannelURL', ''),
            'user_channel_id': channel.get('UserChannelID', ''),
            'time_shift': channel.get('TimeShift', ''),
            'channel_sdp_url': channel.get('ChannelSDP', ''),
            'channel_logo_url': channel.get('ChannelLogURL', ''),
            'positon': channel.get('Positon', ''),  # 注意：原项目拼写错误
        }


# 示例用法
if __name__ == '__main__':
    # 创建核心实例
    core = TellyGetCore(
        user='0758xxxxxxx',          # IPTV 账号（去掉 @iptv.gd）
        passwd='your_password',       # IPTV 密码
        mac='XX:D8:F3:73:09:YY'      # 机顶盒 MAC 地址
    )
    
    # 获取频道
    success, result = core.fetch_channels(
        filter_sd=True,                    # 过滤标清频道
        channel_filters=[r'^\d+$']         # 过滤纯数字频道名
    )
    
    if success:
        print(f'成功获取 {len(result)} 个频道')
        
        # 打印前 5 个频道
        for i, channel in enumerate(result[:5], 1):
            info = TellyGetCore.parse_channel_info(channel)
            print(f"{i}. {info['channel_name']} - {info['channel_url']}")
    else:
        print(f'失败: {result}')

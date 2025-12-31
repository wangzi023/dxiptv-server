# IPTV 直播源获取功能文档

## 概述

本项目基于 [tellyget-gd](https://github.com/fejich/tellyget-gd) 改造，核心功能是获取广东电信 IPTV 直播源并保存到数据库。

**原项目 License**: GNU General Public License v3.0

## 功能特点

1. ✅ 认证广东电信 IPTV 账户
2. ✅ 自动获取所有频道列表
3. ✅ 解析频道信息（名称、ID、URL、Logo 等）
4. ✅ 保存到数据库（而不是生成 m3u 文件）
5. ✅ 自动过滤标清频道（当有高清版本时）
6. ✅ 支持自定义频道名称过滤器

## 核心模块

### 1. `app/utils/tellyget_core.py`

核心模块，包含以下类：

- **Cipher**: DES3 加密/解密工具
- **Authenticator**: IPTV 认证器，构建认证信息
- **IPTVAuth**: 认证类，处理登录流程
- **IPTVChannelFetcher**: 频道获取器，解析频道列表
- **TellyGetCore**: 对外接口，封装完整功能

### 2. `app/services/iptv_service.py`

服务层，包含：

- **IPTVService**: 业务逻辑，包括：
  - `fetch_and_save_channels()`: 获取并保存频道
  - `get_channels_by_source()`: 查询频道列表
  - `update_channel_status()`: 更新频道状态
  - `delete_channels_by_source()`: 删除频道
  - `get_channel_statistics()`: 获取统计信息

### 3. `app/routes/iptv.py`

API 路由，提供以下接口：

```
POST   /api/iptv/fetch                      # 获取并保存频道
GET    /api/iptv/channels/<source_id>       # 获取频道列表
PUT    /api/iptv/channels/<channel_id>/status  # 更新频道状态
DELETE /api/iptv/channels/source/<source_id>   # 删除所有频道
GET    /api/iptv/statistics/<source_id>    # 获取统计信息
```

## 数据库结构

### accounts 表（账户）

```sql
CREATE TABLE accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,      -- IPTV 账号（如：0758xxxxxxx@iptv.gd）
    password TEXT NOT NULL,              -- IPTV 密码
    mac TEXT NOT NULL,                   -- 机顶盒 MAC 地址
    imei TEXT,                           -- IMEI（可选）
    address TEXT,                        -- IP 地址（可选）
    source_id INTEGER,                   -- 关联的直播源 ID
    last_fetch_time DATETIME,            -- 最后获取时间
    last_fetch_status TEXT,              -- 最后获取状态
    status TEXT DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### sources 表（直播源）

```sql
CREATE TABLE sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                  -- 直播源名称
    account_id INTEGER,                  -- 关联的账户 ID
    channel_count INTEGER DEFAULT 0,     -- 频道数量
    last_updated DATETIME,               -- 最后更新时间
    status TEXT DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### channels 表（频道）

```sql
CREATE TABLE channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id TEXT NOT NULL,            -- 频道 ID
    channel_name TEXT NOT NULL,          -- 频道名称
    channel_url TEXT NOT NULL,           -- 频道 URL（RTSP/HTTP）
    user_channel_id TEXT,                -- 用户频道 ID
    time_shift TEXT,                     -- 时移信息
    channel_sdp_url TEXT,                -- SDP URL
    channel_logo_url TEXT,               -- Logo URL
    positon TEXT,                        -- 位置信息
    source_id INTEGER,                   -- 关联的直播源 ID
    category TEXT,                       -- 分类
    status INTEGER DEFAULT 1,            -- 状态（1: 启用, 0: 禁用）
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 使用指南

### 1. 命令行测试

运行测试脚本验证核心功能：

```bash
cd d:\itcast\dxiptv-server
python tests/test_tellyget.py
```

按提示输入：
- 账号（不含 @iptv.gd 后缀，如：0758xxxxxxx）
- 密码
- MAC 地址（如：XX:D8:F3:73:09:YY）

### 2. API 调用

#### 2.1 获取并保存频道

```bash
POST /api/iptv/fetch
Content-Type: application/json
Authorization: Bearer <token>

{
    "account_id": 1,
    "filter_sd": true,           # 可选，默认 true
    "channel_filters": []        # 可选，正则表达式数组
}
```

响应：

```json
{
    "success": true,
    "message": "成功保存 100 个频道",
    "channel_count": 100
}
```

#### 2.2 获取频道列表

```bash
GET /api/iptv/channels/1?status=1
Authorization: Bearer <token>
```

响应：

```json
{
    "success": true,
    "channels": [
        {
            "id": 1,
            "channel_id": "1",
            "channel_name": "CCTV1高清",
            "channel_url": "rtsp://...",
            "channel_logo_url": "http://...",
            "status": 1,
            "created_at": "2024-01-01 00:00:00",
            "updated_at": "2024-01-01 00:00:00"
        }
    ]
}
```

#### 2.3 更新频道状态

```bash
PUT /api/iptv/channels/1/status
Content-Type: application/json
Authorization: Bearer <token>

{
    "status": 0  # 0: 禁用, 1: 启用
}
```

#### 2.4 获取统计信息

```bash
GET /api/iptv/statistics/1
Authorization: Bearer <token>
```

响应：

```json
{
    "success": true,
    "statistics": {
        "total": 100,
        "active": 90,
        "inactive": 10
    }
}
```

### 3. Python 代码示例

```python
from app.utils.tellyget_core import TellyGetCore

# 创建实例
core = TellyGetCore(
    user='0758xxxxxxx',          # 去掉 @iptv.gd
    passwd='your_password',
    mac='XX:D8:F3:73:09:YY'
)

# 获取频道
success, result = core.fetch_channels(
    filter_sd=True,              # 过滤标清频道
    channel_filters=[r'^\d+$']   # 过滤纯数字频道名
)

if success:
    channels = result
    print(f'获取到 {len(channels)} 个频道')
    
    for channel in channels:
        info = TellyGetCore.parse_channel_info(channel)
        print(f"{info['channel_name']}: {info['channel_url']}")
else:
    print(f'失败: {result}')
```

## 技术细节

### 认证流程

1. **获取 Base URL**
   ```
   GET http://eds.iptv.gd.cn:8082/EDS/jsp/AuthenticationURL?UserID=xxx&Action=Login
   跟随 302 重定向，提取 base_url
   ```

2. **获取 Token**
   ```
   GET {base_url}/EPG/oauth/v2/authorize?response_type=EncryToken&client_id=smcphone&userid=xxx
   返回: {"EncryToken": "..."}
   ```

3. **构建认证信息**
   ```
   明文: random$token$user$imei$ip$mac$$CTC
   密钥: MD5(password)[:24].upper()
   加密: DES3 ECB 模式
   ```

4. **登录**
   ```
   GET {base_url}/EPG/oauth/v2/token?authinfo=...&grant_type=EncryToken&...
   ```

### 频道获取流程

1. **请求频道列表**
   ```
   POST {base_url}/EPG/jsp/getchannellistHWCTC.jsp
   ```

2. **解析 HTML**
   - 使用 BeautifulSoup 解析
   - 查找 `<script>` 标签中的 `ChannelID="..."`
   - 提取 JavaScript 配置：`Authentication.CTCSetConfig('Channel','...')`

3. **解析频道参数**
   ```javascript
   ChannelID="1" ChannelName="CCTV1高清" ChannelURL="rtsp://..." ...
   ```

4. **过滤处理**
   - 应用自定义过滤器（正则匹配）
   - 移除标清候选（如果有高清版本）

## 依赖项

```txt
Flask==3.0.0
Flask-CORS==4.0.0
beautifulsoup4==4.12.2       # HTML 解析
pycryptodome==3.19.0         # DES3 加密
requests==2.31.0             # HTTP 请求
requests-toolbelt==1.0.0     # Socket 绑定
PyJWT==2.8.0
Werkzeug==3.0.1
```

## 注意事项

1. **账号格式**
   - 数据库存储：完整账号（如：0758xxxxxxx@iptv.gd）
   - 认证使用：去掉后缀（如：0758xxxxxxx）
   - 代码会自动处理转换

2. **MAC 地址**
   - 必须是真实机顶盒的 MAC 地址
   - 格式：`XX:D8:F3:73:09:YY`

3. **频道 URL**
   - 大多是 RTSP 协议
   - 部分可能是 HTTP 协议
   - 需要支持对应协议的播放器

4. **License**
   - 本项目基于 tellyget-gd（GPL v3.0）
   - 修改后的代码也遵循 GPL v3.0
   - 允许商业使用，但必须开源

## 故障排查

### 认证失败

1. 检查账号密码是否正确
2. 检查 MAC 地址是否正确
3. 检查网络连接
4. 查看日志文件：`logs/tellyget_core.log`

### 频道获取失败

1. 确认认证成功
2. 检查是否被服务器限流
3. 查看返回的 HTML 内容
4. 检查正则表达式匹配

### 数据库保存失败

1. 检查 source_id 是否正确
2. 确认频道数据格式正确
3. 查看数据库错误日志

## 后续开发建议

1. **前端界面**
   - 账户管理页面
   - 频道列表展示
   - 一键获取按钮
   - 状态实时更新

2. **功能增强**
   - 定时自动更新
   - 频道分类管理
   - 频道搜索功能
   - 批量操作

3. **性能优化**
   - 异步任务队列
   - 缓存机制
   - 批量插入优化

4. **监控告警**
   - 账户状态监控
   - 获取失败告警
   - 频道可用性检测

## 开源协议

```
GNU General Public License v3.0

This project is based on tellyget-gd (https://github.com/fejich/tellyget-gd)
which is licensed under GNU GPL v3.0.

You are free to:
- Use commercially
- Modify
- Distribute
- Patent use
- Private use

Under the following terms:
- Disclose source
- License and copyright notice
- Same license
- State changes
```

## 联系方式

如有问题或建议，请联系项目维护者。

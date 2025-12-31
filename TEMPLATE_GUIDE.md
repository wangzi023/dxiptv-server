# 频道模板管理系统使用指南

## 系统概述

频道模板管理系统是一个独立的模块，用于管理IPTV频道的标准信息（channel_id、名称、分组）。系统会根据电信接口返回的`ChannelID`自动匹配模板库，为频道补充标准名称和分组信息。

### 核心功能

1. **自动匹配**：获取频道时，系统自动根据`channel_id`匹配模板库
2. **标准化管理**：统一管理176个频道模板（广东电信IPTV）
3. **分类体系**：支持6大分类（广东、央视、卫视、4K超高清、付费、其他）
4. **未分类处理**：未匹配的频道自动归类为"未分类"

## 数据库设计

### channel_template 表

```sql
CREATE TABLE channel_template (
    id INTEGER PRIMARY KEY,                    -- 模板ID
    channel_id TEXT NOT NULL UNIQUE,          -- 频道ID（电信接口返回）
    name TEXT NOT NULL,                        -- 标准频道名称
    group_title TEXT NOT NULL,                 -- 分组名称
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**特点**：
- `id` 和 `channel_id` 都不重复
- `channel_id` 作为匹配键，对应电信接口的 `ChannelID`
- 初始化时自动导入 `public/data.json` 的176个频道

## 使用场景

### 场景1：自动匹配频道信息

**触发时机**：调用 `/api/iptv/fetch` 获取频道时

**匹配逻辑**：
```python
# 电信接口返回：ChannelID = "6197"
# 模板库查询：channel_id = "6197"
# 匹配结果：name = "广东卫视", group_title = "广东"

# 如果未匹配到：
# name = 原始频道名称（电信接口返回）
# group_title = "未分类"
```

**效果**：
- 匹配成功：频道使用模板的标准名称和分组
- 未匹配：显示原始名称，分组显示"未分类"

### 场景2：管理频道模板

#### 查看模板列表

1. 登录系统，点击左侧菜单"频道模板"
2. 查看统计信息：
   - 模板总数：176个
   - 分类统计：各分类的频道数量
3. 筛选功能：按分组筛选模板列表

#### 添加新模板

1. 点击"添加模板"按钮
2. 填写信息：
   - **频道ID**：必填，电信接口返回的ChannelID
   - **频道名称**：必填，标准频道名称
   - **分组**：必填，从现有分组中选择
3. 保存

**注意**：频道ID不能重复，系统会自动检查

#### 编辑模板

1. 在模板列表中点击"编辑"按钮
2. 修改信息（频道ID不可修改）
3. 保存

#### 删除模板

1. 在模板列表中点击"删除"按钮
2. 确认删除

## API 接口文档

### 1. 获取模板列表

**请求**：
```http
GET /api/channel-template/templates?group_title=广东
Authorization: Bearer <token>
```

**响应**：
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "channel_id": "6197",
      "name": "广东卫视",
      "group_title": "广东",
      "created_at": "2025-12-31 02:09:41",
      "updated_at": "2025-12-31 02:09:41"
    }
  ]
}
```

### 2. 获取单个模板

**请求**：
```http
GET /api/channel-template/templates/1
Authorization: Bearer <token>
```

**响应**：
```json
{
  "success": true,
  "data": {
    "id": 1,
    "channel_id": "6197",
    "name": "广东卫视",
    "group_title": "广东"
  }
}
```

### 3. 获取分组列表

**请求**：
```http
GET /api/channel-template/groups
Authorization: Bearer <token>
```

**响应**：
```json
{
  "success": true,
  "data": ["广东", "央视", "卫视", "4K超高清", "付费", "其他"]
}
```

### 4. 获取统计信息

**请求**：
```http
GET /api/channel-template/statistics
Authorization: Bearer <token>
```

**响应**：
```json
{
  "success": true,
  "data": {
    "total": 176,
    "groups": {
      "广东": 67,
      "央视": 39,
      "卫视": 34,
      "其他": 20,
      "4K超高清": 12,
      "付费": 4
    }
  }
}
```

### 5. 添加模板

**请求**：
```http
POST /api/channel-template/templates
Authorization: Bearer <token>
Content-Type: application/json

{
  "channel_id": "12345",
  "name": "测试频道",
  "group_title": "其他"
}
```

**响应**：
```json
{
  "success": true,
  "message": "添加成功",
  "id": 177
}
```

### 6. 更新模板

**请求**：
```http
PUT /api/channel-template/templates/177
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "测试频道2",
  "group_title": "广东"
}
```

**响应**：
```json
{
  "success": true,
  "message": "更新成功"
}
```

### 7. 删除模板

**请求**：
```http
DELETE /api/channel-template/templates/177
Authorization: Bearer <token>
```

**响应**：
```json
{
  "success": true,
  "message": "删除成功"
}
```

### 8. 匹配频道信息

**请求**：
```http
GET /api/channel-template/match/6197
Authorization: Bearer <token>
```

**响应**：
```json
{
  "success": true,
  "data": {
    "name": "广东卫视",
    "group_title": "广东"
  }
}
```

未匹配时：
```json
{
  "success": true,
  "data": {
    "name": null,
    "group_title": "未分类"
  }
}
```

## 技术实现

### 后端架构

```
app/
├── models/
│   └── channel_template.py          # 数据库模型
├── services/
│   ├── channel_template_service.py  # 业务逻辑
│   └── iptv_service.py              # 集成模板匹配
└── routes/
    └── channel_template.py          # API路由
```

### 核心代码

**自动匹配逻辑** (`iptv_service.py`):
```python
# 使用模板匹配频道名称和分组
channel_id = parsed['channel_id']
match_info = ChannelTemplateService.match_channel_info(channel_id)

# 使用匹配结果或原始信息
final_name = match_info['name'] if match_info['name'] else parsed['channel_name']
final_category = match_info['group_title']  # "未分类" 或实际分类
```

**匹配服务** (`channel_template_service.py`):
```python
@staticmethod
def match_channel_info(channel_id):
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
```

## 常见问题

### Q1: 如何更新模板库数据？

A: 修改 `public/data.json` 文件，然后：
1. 删除数据库文件 `data/iptv.db` 或删除 `channel_template` 表
2. 重启应用，系统会自动重新导入

### Q2: 可以批量导入模板吗？

A: 是的，编辑 `public/data.json`，添加新的频道条目：
```json
{
  "id": 177,
  "channel_id": "新频道ID",
  "name": "频道名称",
  "group_title": "分组"
}
```

### Q3: 如何添加新的分组？

A: 直接在添加/编辑模板时使用新的分组名称即可，系统会自动识别

### Q4: 已有频道如何批量更新分类？

A: 
1. 更新模板库中的数据
2. 重新获取频道（调用 `/api/iptv/fetch`）
3. 系统会自动应用新的分类

### Q5: 为什么有些频道显示"未分类"？

A: 两个原因：
1. 模板库中没有该频道的 `channel_id`
2. 该频道是新增的，尚未添加到模板库

**解决方法**：在"频道模板"页面添加该频道的模板信息

## 数据统计

### 初始化数据

- **总频道数**：176个
- **分类分布**：
  - 广东：67个
  - 央视：39个
  - 卫视：34个
  - 其他：20个
  - 4K超高清：12个
  - 付费：4个

### 覆盖范围

系统预装了广东电信IPTV的完整频道表，覆盖：
- 广东本地频道（广州、深圳、佛山等）
- 中央电视台（CCTV-1至CCTV-17及数字频道）
- 各省卫视
- 4K超高清频道
- 专业付费频道

## 最佳实践

1. **定期维护**：定期检查"未分类"频道，及时添加到模板库
2. **命名规范**：使用标准的频道名称，便于用户识别
3. **分组合理**：按照地域、类型等维度合理分组
4. **ID管理**：添加新模板时，使用递增的ID（系统自动分配）

## 升级记录

### v1.0.0 (2025-12-31)

- ✅ 创建 `channel_template` 数据库表
- ✅ 实现频道模板服务层
- ✅ 提供完整的 REST API
- ✅ 集成到 IPTV 频道获取流程
- ✅ 前端管理界面
- ✅ 自动导入初始数据（176个频道）
- ✅ 支持增删改查操作
- ✅ 自动匹配和未分类处理

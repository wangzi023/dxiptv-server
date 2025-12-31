# 频道导出功能使用说明

## 功能概述

在频道管理页面新增了"导出文本"功能，可以将频道列表导出为标准的IPTV频道列表格式文本文件。

## 导出格式

导出的文本文件格式如下：

```
央视,#genre#
CCTV1,rtsp://xxx
CCTV2,rtsp://xxx
广东,#genre#
广东卫视,rtsp://xxx
广东珠江,rtsp://xxx
卫视,#genre#
湖南卫视,rtsp://xxx
浙江卫视,rtsp://xxx
```

## 使用方法

### 1. 导出全部频道

1. 进入"频道管理"页面
2. 确保筛选条件都是"所有账户"和"所有分类"
3. 点击"导出文本"按钮
4. 文件将自动下载为 `channels.txt`

### 2. 按分类导出

1. 进入"频道管理"页面
2. 在"分类"下拉框中选择要导出的分类（如"央视"）
3. 点击"导出文本"按钮
4. 文件将自动下载为 `channels_央视.txt`

### 3. 按账户导出

1. 进入"频道管理"页面
2. 在"账户"下拉框中选择要导出的账户
3. 点击"导出文本"按钮
4. 文件将自动下载为 `channels_账户名.txt`

### 4. 按账户和分类导出

1. 进入"频道管理"页面
2. 同时选择账户和分类
3. 点击"导出文本"按钮
4. 文件将自动下载为 `channels_分类_账户名.txt`

## 文本格式说明

### 分类标记

每个分类以 `,#genre#` 结尾作为标记：
```
央视,#genre#
```

### 频道格式

每个频道一行，格式为 `频道名称,频道URL`：
```
CCTV1,rtsp://xxx
```

### 排序规则

- 按分类字母顺序排列
- 同一分类内按频道名称排列

### 未分类频道

没有分类的频道会归类到"未分类"：
```
未分类,#genre#
测试频道,rtsp://xxx
```

## API 接口

### 请求

```http
GET /api/iptv/channels/export?source_id=1&category=央视
Authorization: Bearer <token>
```

**参数说明**：
- `source_id`（可选）：源ID，对应账户的直播源
- `category`（可选）：分类名称

**示例**：
```bash
# 导出全部
curl -H "Authorization: Bearer <token>" \
  http://localhost:3000/api/iptv/channels/export > channels.txt

# 导出央视频道
curl -H "Authorization: Bearer <token>" \
  http://localhost:3000/api/iptv/channels/export?category=央视 > cctv.txt

# 导出指定账户的频道
curl -H "Authorization: Bearer <token>" \
  http://localhost:3000/api/iptv/channels/export?source_id=1 > account1.txt
```

### 响应

**成功**：
```
HTTP/1.1 200 OK
Content-Type: text/plain; charset=utf-8
Content-Disposition: attachment; filename=channels.txt

央视,#genre#
CCTV1,rtsp://xxx
...
```

**失败**：
```json
{
  "success": false,
  "message": "系统异常: xxx"
}
```

## 使用场景

### 1. 备份频道列表

定期导出频道列表，作为备份保存。

### 2. 分享频道源

导出特定分类的频道，分享给其他用户。

### 3. IPTV播放器导入

导出的文本文件可以直接导入到支持M3U格式的IPTV播放器中。

### 4. 频道对比

导出不同账户的频道列表，进行对比分析。

## 注意事项

1. **权限要求**：需要登录并具有有效的JWT Token
2. **编码格式**：导出文件使用UTF-8编码
3. **文件大小**：根据频道数量，文件大小从几KB到几MB不等
4. **筛选条件**：导出时会应用当前的筛选条件
5. **空数据处理**：如果没有符合条件的频道，将导出空文件

## 常见问题

### Q1: 导出的文件乱码怎么办？

A: 确保使用支持UTF-8编码的文本编辑器打开文件，如：
- Windows: Notepad++、VS Code
- Mac: TextEdit、VS Code
- Linux: gedit、vim

### Q2: 可以批量导出多个分类吗？

A: 目前不支持。如需导出多个分类，请分别导出后手动合并。

### Q3: 导出的URL格式是什么？

A: 导出的是数据库中存储的原始URL，通常是RTSP或HTTP协议的流媒体地址。

### Q4: 如何修改导出格式？

A: 如需自定义格式，请修改后端代码 `app/routes/iptv.py` 中的 `export_channels` 函数。

### Q5: 导出速度慢怎么办？

A: 导出速度取决于频道数量。如果频道过多，建议：
- 按分类分批导出
- 按账户分批导出
- 优化数据库索引

## 技术实现

### 后端实现

**文件**: `app/routes/iptv.py`

```python
@iptv_bp.route('/channels/export', methods=['GET'])
@token_required
def export_channels():
    # 1. 获取筛选条件
    source_id = request.args.get('source_id', type=int)
    category = request.args.get('category')
    
    # 2. 查询数据库
    channels = execute_query(sql, params)
    
    # 3. 按分类分组
    grouped = {}
    for channel in channels:
        cat = channel['category'] or '未分类'
        grouped[cat].append(channel)
    
    # 4. 生成文本
    lines = []
    for cat in sorted(grouped.keys()):
        lines.append(f"{cat},#genre#")
        for channel in grouped[cat]:
            lines.append(f"{channel['channel_name']},{channel['channel_url']}")
    
    # 5. 返回文件
    return '\n'.join(lines), 200, {
        'Content-Type': 'text/plain; charset=utf-8',
        'Content-Disposition': 'attachment; filename=channels.txt'
    }
```

### 前端实现

**文件**: `public/app.js`

```javascript
async function exportChannels() {
    // 1. 获取筛选条件
    const sourceId = accountFilter.value;
    const category = categoryFilter.value;
    
    // 2. 构建URL
    const url = `${API_BASE_URL}/iptv/channels/export?...`;
    
    // 3. 下载文件
    const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    
    const blob = await response.blob();
    
    // 4. 触发下载
    const a = document.createElement('a');
    a.href = window.URL.createObjectURL(blob);
    a.download = 'channels.txt';
    a.click();
}
```

## 更新日志

### v1.0.0 (2025-12-31)

- ✅ 新增频道导出功能
- ✅ 支持按分类导出
- ✅ 支持按账户导出
- ✅ 支持组合筛选导出
- ✅ 自动生成文件名
- ✅ 标准IPTV频道列表格式
- ✅ UTF-8编码支持

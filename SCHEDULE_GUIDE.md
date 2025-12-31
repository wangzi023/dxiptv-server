# 定时任务系统 - 使用指南

## 概述

定时任务系统允许用户设置自动化任务，在指定的时间自动获取直播源并更新到数据库。系统支持多种重复类型，包括每天、每周、每月以及仅执行一次。

## 功能特性

✅ **灵活的定时调度**
- 支持每天、每周、每月、仅一次四种重复类型
- 支持自定义执行时间 (HH:MM 格式)
- 支持启用/禁用任务

✅ **与直播源获取集成**
- 自动调用核心服务获取最新直播源
- 支持频道过滤（通过频道名称）
- 支持过滤标清频道

✅ **完整的任务管理**
- 创建、编辑、删除任务
- 查看任务执行历史和状态
- 实时显示下次执行时间

## 核心组件

### 1. 调度器 (Scheduler)
**文件**: `app/utils/scheduler.py`

负责任务的定时执行：
- `Scheduler`: 主要调度器类，管理所有任务
- `Task`: 单个任务的表示
- `get_scheduler()`: 获取全局调度器实例
- `init_scheduler()`: 初始化调度器

```python
# 获取调度器
from app.utils.scheduler import get_scheduler

scheduler = get_scheduler()

# 添加任务
task = Task(
    task_id=1,
    task_type='fetch_channels',
    account_id=1,
    schedule_time='14:30',
    is_enabled=True,
    repeat_type='daily'
)
scheduler.add_task(task)

# 启动调度器
scheduler.start()
```

### 2. 任务管理服务 (ScheduleService)
**文件**: `app/services/schedule_service.py`

提供任务的 CRUD 操作：

```python
from app.services import ScheduleService

# 创建任务
result = ScheduleService.create_task(
    account_id=1,
    task_type='fetch_channels',
    schedule_time='14:30',
    repeat_type='daily',
    filter_sd=True,
    channel_filters='cctv'
)

# 获取所有任务
tasks = ScheduleService.get_all_tasks(account_id=1)

# 更新任务
ScheduleService.update_task(task_id=1, schedule_time='15:00')

# 启用/禁用任务
ScheduleService.enable_task(task_id=1)
ScheduleService.disable_task(task_id=1)

# 删除任务
ScheduleService.delete_task(task_id=1)
```

### 3. API 路由
**文件**: `app/routes/schedule.py`

#### 创建任务
```
POST /api/schedule/tasks
Authorization: Bearer <token>
Content-Type: application/json

{
  "account_id": 1,
  "task_type": "fetch_channels",
  "schedule_time": "14:30",
  "repeat_type": "daily",
  "filter_sd": true,
  "channel_filters": "cctv,hd"
}
```

**响应**:
```json
{
  "success": true,
  "message": "任务创建成功",
  "task": {
    "id": 1,
    "account_id": 1,
    "task_type": "fetch_channels",
    "schedule_time": "14:30",
    "repeat_type": "daily",
    "is_enabled": 1,
    "created_at": "2025-12-30 12:58:54"
  }
}
```

#### 获取任务列表
```
GET /api/schedule/tasks?account_id=1
Authorization: Bearer <token>
```

**响应**:
```json
{
  "success": true,
  "message": "获取任务列表成功",
  "count": 1,
  "tasks": [...]
}
```

#### 获取单个任务
```
GET /api/schedule/tasks/{task_id}
Authorization: Bearer <token>
```

#### 更新任务
```
PUT /api/schedule/tasks/{task_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "schedule_time": "15:00",
  "repeat_type": "weekly"
}
```

#### 启用/禁用任务
```
PUT /api/schedule/tasks/{task_id}/enable
PUT /api/schedule/tasks/{task_id}/disable
Authorization: Bearer <token>
```

#### 删除任务
```
DELETE /api/schedule/tasks/{task_id}
Authorization: Bearer <token>
```

### 4. 前端界面
**文件**: `public/schedule.html`

提供用户友好的界面来管理定时任务：
- 创建新任务表单
- 任务列表展示
- 编辑、启用/禁用、删除操作
- 实时任务状态显示

## 数据库表结构

```sql
CREATE TABLE schedule_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    task_type TEXT NOT NULL,
    schedule_time TEXT NOT NULL,           -- HH:MM 格式
    repeat_type TEXT DEFAULT 'daily',      -- once, daily, weekly, monthly
    filter_sd INTEGER DEFAULT 1,           -- 是否过滤标清
    channel_filters TEXT,                  -- 频道过滤器
    is_enabled INTEGER DEFAULT 1,          -- 是否启用
    last_executed DATETIME,                -- 上次执行时间
    next_execution DATETIME,               -- 下次执行时间
    execution_count INTEGER DEFAULT 0,     -- 执行次数
    last_error TEXT,                       -- 最后一次错误
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
)
```

## 工作流程

```
┌─────────────────────────────────────────────────┐
│         用户在前端创建定时任务                    │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│    POST /api/schedule/tasks (API)               │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│  ScheduleService.create_task()                  │
│  - 验证参数                                      │
│  - 保存到数据库                                  │
│  - 添加到调度器                                  │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│  Scheduler 运行循环                             │
│  - 每60秒检查一次                                │
│  - 检查是否有任务需要执行                        │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│  执行任务回调函数                                │
│  - 调用 IPTVService.fetch_and_save_channels()   │
│  - 获取直播源                                    │
│  - 保存到数据库                                  │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│  更新任务执行状态                                │
│  - 更新 last_executed                            │
│  - 计算 next_execution                           │
│  - 更新 execution_count                          │
└─────────────────────────────────────────────────┘
```

## 使用示例

### 创建每日早上8点的定时任务

```javascript
// 前端代码
const token = localStorage.getItem('token');

fetch('/api/schedule/tasks', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    account_id: 1,
    task_type: 'fetch_channels',
    schedule_time: '08:00',
    repeat_type: 'daily',
    filter_sd: true,
    channel_filters: 'cctv'
  })
})
.then(res => res.json())
.then(data => {
  if (data.success) {
    console.log('任务创建成功:', data.task);
  }
});
```

### 编程方式创建任务

```python
# 后端代码
from app.services import ScheduleService

result = ScheduleService.create_task(
    account_id=1,
    task_type='fetch_channels',
    schedule_time='08:00',
    repeat_type='daily',
    filter_sd=True,
    channel_filters='cctv'
)

if result['success']:
    task = result['task']
    print(f"任务创建成功，ID: {task['id']}")
```

## 重复类型说明

| 类型 | 说明 | 示例 |
|------|------|------|
| `once` | 仅执行一次 | 设置后在指定时间执行一次，之后不再执行 |
| `daily` | 每天 | 每天在指定时间执行 |
| `weekly` | 每周 | 每周同一天的指定时间执行 |
| `monthly` | 每月 | 每月同一日期的指定时间执行 |

## 配置说明

### 调度器检查间隔

在 `app/factory.py` 中初始化调度器时可设置检查间隔：

```python
init_scheduler(check_interval=60)  # 每60秒检查一次
```

较小的值会更及时执行任务，但会增加 CPU 使用。建议设置为 60-300 秒。

### 任务执行回调

在 `app/factory.py` 的 `_register_task_callbacks()` 函数中注册任务类型的执行逻辑：

```python
def fetch_channels_callback(task):
    """获取直播源回调"""
    result = IPTVService.fetch_and_save_channels(
        account_id=task.account_id,
        filter_sd=task.filter_sd,
        channel_filters=task.channel_filters
    )
    logger.info(f'任务 {task.task_id} 执行结果: {result}')

scheduler.register_callback('fetch_channels', fetch_channels_callback)
```

## 常见问题

### Q: 任务没有执行
**A**: 请检查以下几点：
1. 任务是否启用（`is_enabled = 1`）
2. 调度器是否正在运行（查看应用日志）
3. 执行时间是否已过（检查 `next_execution`）
4. 账户 ID 是否存在

### Q: 如何修改已创建任务的时间
**A**: 使用 API 更新任务：
```
PUT /api/schedule/tasks/{task_id}
{
  "schedule_time": "新时间"
}
```

### Q: 任务执行失败如何处理
**A**: 查看数据库中 `last_error` 字段获取错误信息，根据错误消息修复问题后重新启用任务。

### Q: 支持多少个任务
**A**: 理论上无限制，但实际受调度器性能限制。通常建议不超过 1000 个并发任务。

## 日志输出

应用启动时会输出：
```
2025-12-30 20:57:43 - iptv-system - INFO - 定时任务调度器初始化成功
2025-12-30 20:57:43 - iptv-system - INFO - 任务回调已注册
```

任务执行时会输出：
```
2025-12-30 21:00:00 - scheduler - INFO - 执行定时任务: 1 (fetch_channels)
2025-12-30 21:00:05 - task_executor - INFO - 任务 1 执行结果: {'success': True, 'message': '成功保存 50 个频道', 'channel_count': 50}
```

## 总结

定时任务系统完全集成在应用中，提供了强大而灵活的定时执行能力。通过简单的 API 和友好的前端界面，用户可以轻松设置和管理定时任务，实现自动化的直播源更新流程。

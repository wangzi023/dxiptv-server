# 🔄 工程化迁移指南

## 📌 概述

项目已完成工程化重构，从单体 `app.py` 文件升级为模块化架构。新的应用入口是 `app_new.py`。

## 🚀 快速开始

### 1. 启动新应用
```bash
# 停止旧应用（如果运行中）
# Ctrl+C

# 启动新应用（开发模式）
python app_new.py

# 或指定端口
python app_new.py --port 3000

# 或生产模式
python app_new.py --production
```

### 2. 应用已启动
```
正在启动应用... (环境: DevelopmentConfig)
数据库初始化完成
应用启动完成
应用启动在 http://0.0.0.0:3000
按 Ctrl+C 停止服务器
```

## 🔄 从旧应用迁移

### 旧应用（app.py）
- ❌ 不再维护
- ❌ 代码混乱
- ✅ 保留用于参考

### 新应用（app_new.py）
- ✅ 工程化设计
- ✅ 模块化架构
- ✅ 易于维护和扩展

### 完全迁移步骤

#### 步骤 1：备份旧应用
```bash
# 备份原始 app.py
copy app.py app_backup.py
```

#### 步骤 2：配置新应用
```bash
# 复制配置（config.py 已创建）
# 无需其他操作，所有依赖已在新应用中
```

#### 步骤 3：测试新应用
```bash
# 1. 启动新应用
python app_new.py

# 2. 测试登录
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin@123"}'

# 3. 应该返回令牌和用户信息
```

#### 步骤 4：更新启动脚本

**Windows (start.bat)**
```batch
@echo off
cd /d %~dp0
python app_new.py --host 0.0.0.0 --port 3000
pause
```

**Linux/Mac (start.sh)**
```bash
#!/bin/bash
cd "$(dirname "$0")"
python app_new.py --host 0.0.0.0 --port 3000
```

#### 步骤 5：删除旧应用（可选）
```bash
# 确认新应用工作正常后，可删除旧应用
del app.py
del database.py  # 数据库逻辑已整合到 app/models/
```

## 📊 变更对比

| 方面 | 旧应用 (app.py) | 新应用 (app_new.py) |
|------|-----------------|----------------------|
| **文件大小** | ~800 行 | ~50 行 (入口) |
| **代码结构** | 单体 | 模块化 |
| **配置管理** | 内嵌常数 | 独立 config.py |
| **业务逻辑** | 混合路由 | 独立 Services |
| **工具函数** | 散落各处 | 统一 Utils |
| **日志系统** | 无 | 完整的日志系统 |
| **可维护性** | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **可扩展性** | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **可测试性** | ⭐ | ⭐⭐⭐⭐⭐ |

## 🔧 常见问题

### Q1: 新应用的数据库文件在哪里？
**A:** 仍然在 `data/iptv.db`，完全兼容。

### Q2: 前端需要修改吗？
**A:** 不需要！所有 API 端点保持不变。

### Q3: 配置如何修改？
**A:** 编辑 `config.py`，支持开发/生产/测试三种环境。

### Q4: 如何添加新功能？
**A:** 参考 `PROJECT_STRUCTURE.md` 中的"添加新功能步骤"。

### Q5: 如何迁移现有的业务模块？
**A:** 
1. 从 `app.py` 中提取业务逻辑
2. 创建新的 Service 类
3. 创建对应的路由 Blueprint
4. 注册蓝图

### Q6: 旧的 app.py 还能用吗？
**A:** 可以，但建议迁移到新应用。

## 📝 文件对应关系

| 旧文件/函数 | 新位置 |
|-----------|--------|
| `database.py` | `app/models/database.py` |
| `hash_password()` | `app/utils/auth.py` |
| `generate_token()` | `app/utils/auth.py` |
| `verify_token()` | `app/utils/auth.py` |
| `token_required()` | `app/utils/auth.py` |
| `/api/auth/*` 路由 | `app/routes/auth.py` |
| `/api/admins/*` 路由 | `app/routes/admin.py` |

## 🎯 迁移检查清单

- [ ] 备份原始应用
- [ ] 测试新应用启动
- [ ] 测试登录功能
- [ ] 测试管理员管理功能
- [ ] 更新启动脚本
- [ ] 验证前端可正常访问
- [ ] 验证所有 API 端点正常
- [ ] 检查日志生成（`logs/iptv-system.log`）
- [ ] 删除旧应用（可选）
- [ ] 提交到版本控制

## 🚨 迁移注意事项

1. **保留数据**
   - 所有数据库数据保留
   - 无需迁移数据

2. **API 兼容**
   - 所有 API 端点保持不变
   - 前端无需修改

3. **环境变量**
   - 可通过 `config.py` 或环境变量配置
   - `FLASK_ENV`: 应用环境（development/production/testing）
   - `JWT_SECRET`: JWT 密钥
   - `SECRET_KEY`: Flask 密钥

4. **日志文件**
   - 自动创建 `logs/` 目录
   - 日志文件: `logs/iptv-system.log`
   - 支持轮转（最多保留 10 个备份）

## 💡 后续改进建议

### 短期（1-2 周）
- [ ] 为所有服务添加单元测试
- [ ] 添加 API 文档（Swagger）
- [ ] 实现缓存层
- [ ] 添加性能监控

### 中期（1-3 个月）
- [ ] 迁移到 ORM（SQLAlchemy）
- [ ] 实现数据库迁移工具（Alembic）
- [ ] 添加消息队列支持
- [ ] 实现异步任务处理

### 长期（3-6 个月）
- [ ] 微服务化
- [ ] 添加 GraphQL 支持
- [ ] 实现高可用方案
- [ ] Docker 容器化

---

**需要帮助？查看 `PROJECT_STRUCTURE.md` 了解完整的架构设计。**

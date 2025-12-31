# 🎬 IPTV 后台管理系统 v3.1.0

## 📖 项目简介

**IPTV后台管理系统**是一个功能完整、易于部署的IPTV频道管理解决方案。它提供了账户管理、直播源管理、频道管理、定时任务等核心功能，帮助您高效地管理IPTV直播源和频道信息。

### 核心特性

✨ **功能完整**
- 账户和源管理
- 频道自动匹配
- 频道导出（支持多种筛选）
- 定时任务调度
- 完整的日志系统

🔐 **安全可靠**
- JWT令牌认证
- 代码混淆加密
- SQLite数据库
- 详细的操作日志

🚀 **易于部署**
- 打包成单一可执行文件
- 跨平台支持
- 自动启动脚本
- 完整的部署文档

📊 **实时监控**
- 系统仪表板
- 实时日志查看
- 统计信息展示
- 定时任务管理

---

## 🛠️ 技术栈

### 后端
- **框架**: Flask 2.x
- **数据库**: SQLite
- **认证**: JWT (PyJWT)
- **任务调度**: APScheduler
- **日志**: Python logging

### 前端
- **框架**: Bootstrap 5
- **图表**: Chart.js
- **通信**: Fetch API

### 打包部署
- **打包工具**: PyInstaller
- **代码混淆**: PyArmor（可选）
- **部署方式**: 独立可执行文件

---

## 📦 项目结构

```
dxiptv-server/
├── app/                          # 应用包
│   ├── __init__.py
│   ├── factory.py               # Flask应用工厂
│   ├── models/                  # 数据模型
│   │   ├── account.py
│   │   ├── source.py
│   │   ├── channel.py
│   │   └── channel_template.py  # 频道模板
│   ├── services/                # 业务逻辑
│   │   ├── iptv_service.py
│   │   ├── log_service.py
│   │   └── channel_template_service.py
│   ├── routes/                  # API路由
│   │   ├── auth.py
│   │   ├── iptv.py
│   │   ├── admin.py
│   │   ├── channel_template.py
│   │   └── ...
│   └── utils/                   # 工具函数
│       ├── auth.py
│       └── ...
├── public/                       # 前端文件
│   ├── index.html               # 主页面
│   ├── login.html               # 登录页
│   ├── app.js                   # 主逻辑
│   └── ...
├── data/                         # 数据目录
│   └── iptv.db                  # SQLite数据库
├── logs/                         # 日志目录
├── build_release.py             # 打包脚本
├── quick_pack.bat               # Windows快速打包
├── quick_pack.sh                # Linux快速打包
├── start.sh                      # Linux启动脚本
├── config.py                     # 配置文件
├── app_new.py                    # 主应用入口
├── requirements.txt              # Python依赖
│
├── 📖 PACKAGING_GUIDE.md         # 打包指南（必读）
├── 📖 DEPLOYMENT_GUIDE.md        # 部署指南（必读）
├── 📖 DEPLOYMENT_CHECKLIST.txt   # 部署检查清单
├── 📖 TEMPLATE_GUIDE.md          # 频道模板使用
├── 📖 CHANNEL_EXPORT_GUIDE.md    # 导出功能使用
└── README.md                     # 本文件
```

---

## 🚀 快速开始

### 前置要求

- **Python 3.7+**
- **pip 包管理工具**
- **Windows 7+ 或 Linux**

### 开发环境运行

```bash
# 1. 克隆或解压项目
cd dxiptv-server

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动应用
python app_new.py

# 4. 打开浏览器
# http://localhost:3000

# 5. 登录
# 用户名: admin
# 密码: adminadmin
```

### 生产环境打包

```bash
# Windows
quick_pack.bat

# Linux/Mac
chmod +x quick_pack.sh
./quick_pack.sh

# 或手动运行
python build_release.py
```

---

## 📚 完整文档

### 核心文档

| 文档 | 说明 | 何时阅读 |
|------|------|---------|
| [PACKAGING_GUIDE.md](PACKAGING_GUIDE.md) | 详细的打包和部署指南 | **首先** |
| [DEPLOYMENT_CHECKLIST.txt](DEPLOYMENT_CHECKLIST.txt) | 分步骤的部署检查清单 | 部署时 |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | 服务器部署详细说明 | 部署时 |
| [TEMPLATE_GUIDE.md](TEMPLATE_GUIDE.md) | 频道模板功能说明 | 使用时 |
| [CHANNEL_EXPORT_GUIDE.md](CHANNEL_EXPORT_GUIDE.md) | 频道导出功能说明 | 使用时 |

### API文档

系统内置完整的REST API，所有接口都在 `/api/` 前缀下：

**认证相关**
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/verify` - 验证令牌
- `POST /api/auth/logout` - 用户登出

**账户管理**
- `GET /api/accounts` - 获取账户列表
- `POST /api/accounts` - 创建账户
- `PUT /api/accounts/{id}` - 更新账户
- `DELETE /api/accounts/{id}` - 删除账户

**频道管理**
- `GET /api/channels` - 获取频道列表
- `GET /api/iptv/channels/export` - 导出频道为文本
- `DELETE /api/channels/{id}` - 删除频道

**频道模板**
- `GET /api/channel-template/templates` - 获取模板列表
- `POST /api/channel-template/templates` - 创建模板
- `PUT /api/channel-template/templates/{id}` - 更新模板
- `DELETE /api/channel-template/templates/{id}` - 删除模板

更多API请查看源代码中的路由定义。

---

## 🔐 安全说明

### 内置安全特性

1. **身份认证**
   - JWT令牌认证
   - 可配置的令牌过期时间
   - 安全的密码存储（SHA256哈希）

2. **代码保护**
   - PyArmor代码混淆（可选）
   - PyInstaller二进制打包
   - 源代码完全隐藏

3. **数据保护**
   - SQLite本地数据库
   - 定期备份建议
   - 日志记录所有操作

### 部署建议

⚠️ **生产环境必做**

- [ ] 修改 `config.ini` 中的JWT密钥
- [ ] 修改数据库文件位置
- [ ] 修改默认admin密码
- [ ] 配置防火墙规则
- [ ] 启用HTTPS（使用反向代理）
- [ ] 定期备份数据
- [ ] 监控日志文件

---

## 💻 系统要求

### 最低配置
- CPU: 1核心
- 内存: 512MB
- 硬盘: 500MB（含数据库空间）
- 网络: 100Mbps

### 推荐配置
- CPU: 2核心以上
- 内存: 2GB以上
- 硬盘: SSD 50GB以上
- 网络: 1Gbps

### 支持的操作系统
- ✅ Windows 7、8、10、11、Server 2008+
- ✅ Linux (Ubuntu、CentOS、Debian等)
- ✅ macOS（可能需要调整）

---

## 📊 功能说明

### 账户管理
管理IPTV播放器或设备账户，包括MAC地址、IMEI、地址等信息。

### 源管理
管理多个IPTV直播源，支持自动获取和手动添加。

### 频道管理
浏览和管理所有可用频道，支持分类筛选和批量操作。

### 频道模板
创建和维护频道模板库，实现自动匹配和分类。

### 频道导出
将频道列表导出为标准IPTV格式（m3u兼容格式），支持灵活筛选。

### 定时任务
设置定期自动获取直播源、更新频道等操作。

### 日志管理
记录所有系统、操作和任务日志，支持查询和下载。

---

## 🐛 故障排除

### 常见问题

**Q: 无法启动应用**
```
A: 检查：
1. Python版本是否 >= 3.7
2. 是否安装了所有依赖: pip install -r requirements.txt
3. 端口3000是否被占用
4. 查看错误日志了解具体错误
```

**Q: 数据库错误**
```
A: 尝试：
1. 检查 data/ 目录权限
2. 删除 data/iptv.db，应用会自动重建
3. 检查磁盘空间是否充足
```

**Q: 忘记管理员密码**
```
A: 恢复步骤：
1. 删除 data/iptv.db
2. 重启应用
3. 使用默认账号登录: admin/adminadmin
```

**Q: 频道列表为空**
```
A: 操作：
1. 前往"源管理" → "获取源"
2. 选择账户，点击"获取"
3. 等待获取完成
4. 前往"频道管理"查看频道
```

更多问题请查看 [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#-故障排除)

---

## 📝 更新日志

### v3.1.0 (2025-12-31)
✨ **新增功能**
- 频道模板管理系统
- 频道导出为文本功能
- 自动频道匹配和分类

🔧 **改进**
- 优化页面加载速度
- 改善错误处理
- 完善文档

🐛 **修复**
- 修复token认证问题
- 修复下拉框加载问题

### v3.0.0 (2025-12-20)
✨ 首个稳定版本发布

---

## 🤝 贡献

欢迎提交Bug报告、功能建议和改进方案！

---

## 📄 许可证

本项目仅供学习和研究使用。

---

## 📞 联系方式

如有问题，请：
1. 查看项目文档
2. 检查日志文件
3. 查看常见问题

---

## 🎯 下一步

### 快速开始三步走

**第一步：打包**
```bash
cd d:\itcast\dxiptv-server
python build_release.py
# 或 quick_pack.bat
```

**第二步：部署**
```bash
# 将 release/ 复制到服务器
# C:\IPTV_Server\
```

**第三步：运行**
```bash
# 在服务器上执行
release\start.bat
# 访问 http://localhost:3000
```

---

## ✅ 完成清单

项目已完成所有核心功能和文档：

- ✅ 完整的后端API
- ✅ 响应式前端界面
- ✅ SQLite数据库
- ✅ 用户认证系统
- ✅ 频道模板管理
- ✅ 频道导出功能
- ✅ 定时任务系统
- ✅ 日志管理
- ✅ 完整的打包脚本
- ✅ 详细的部署文档
- ✅ 故障排除指南

---

**🚀 系统已准备好用于生产环境！**

开始使用：[PACKAGING_GUIDE.md](PACKAGING_GUIDE.md)

# IPTV 系统 - 代码打包和部署指南

## 📦 打包步骤

### 方案选择

我们提供了完整的自动化打包脚本，支持代码混淆、加密和二进制打包。

### 前置要求

1. **安装必要的工具**

```bash
# 安装PyInstaller（打包工具）
pip install pyinstaller

# 安装PyArmor（代码混淆/加密，可选）
pip install pyarmor
```

2. **检查系统环境**

```bash
# 验证Python版本
python --version  # 建议 3.7+

# 验证pip
pip --version
```

### 执行打包

```bash
# 进入项目目录
cd d:\itcast\dxiptv-server

# 运行打包脚本
python build_release.py
```

### 脚本流程

打包脚本会自动执行以下步骤：

1. **检查依赖** ✓
   - 验证PyInstaller是否安装
   - 验证PyArmor是否安装

2. **代码混淆** ✓
   - 使用PyArmor混淆Python代码（可选）
   - 移除不必要的文件
   - 创建临时工作目录

3. **打包成二进制** ✓
   - 使用PyInstaller打包
   - 生成独立可执行文件
   - 包含所有依赖库

4. **创建发布包** ✓
   - 复制可执行文件
   - 生成启动脚本（start.bat）
   - 创建配置示例
   - 创建说明文档

### 输出文件

打包完成后，在 `release/` 目录下会生成：

```
release/
├── iptv-server-3.1.0.exe      # 可执行文件（主程序）
├── start.bat                  # 启动脚本（Windows）
├── config.example.ini         # 配置文件示例
└── README.txt                 # 使用说明
```

## 🚀 部署到服务器

### 步骤 1: 传输文件

```bash
# 将整个 release/ 目录复制到服务器
# 例如：
# 本地: d:\itcast\dxiptv-server\release\
# 服务器: C:\IPTV_Server\
```

### 步骤 2: 启动服务

**方式 A: 直接运行（推荐用于测试）**

```bash
# Windows服务器上
cd C:\IPTV_Server\
start.bat
```

**方式 B: 作为Windows服务运行（生产环境推荐）**

```bash
# 使用NSSM工具注册为Windows服务
# 1. 下载 NSSM: https://nssm.cc/
# 2. 将NSSM.exe放到某个路径

nssm install IPTVServer "C:\IPTV_Server\iptv-server-3.1.0.exe"
nssm set IPTVServer AppDirectory "C:\IPTV_Server"
nssm set IPTVServer AppStdout "C:\IPTV_Server\logs\stdout.log"
nssm set IPTVServer AppStderr "C:\IPTV_Server\logs\stderr.log"

# 启动服务
nssm start IPTVServer

# 停止服务
nssm stop IPTVServer

# 删除服务
nssm remove IPTVServer confirm
```

**方式 C: 使用任务计划程序（开机自启）**

1. 打开 `任务计划程序`
2. 创建基本任务
3. 触发器：系统启动时
4. 操作：启动程序 `iptv-server-3.1.0.exe`
5. 工作目录：`C:\IPTV_Server`

### 步骤 3: 访问应用

```
http://服务器IP:3000
```

默认账号：
- 用户名: `admin`
- 密码: `adminadmin`

### 步骤 4: 防火墙配置

```powershell
# Windows防火墙 - 允许3000端口
netsh advfirewall firewall add rule name="IPTV Server" dir=in action=allow protocol=tcp localport=3000

# 查看规则
netsh advfirewall firewall show rule name="IPTV Server"

# 删除规则
netsh advfirewall firewall delete rule name="IPTV Server"
```

## 📋 配置管理

### 配置文件位置

```
release/data/iptv.db        # SQLite数据库
release/logs/               # 日志目录
```

### 修改配置（如需要）

编辑 `config.example.ini` 并重命名为 `config.ini`:

```ini
[server]
host = 0.0.0.0          # 监听地址
port = 3000             # 监听端口

[jwt]
secret = your-secret-key  # 修改JWT密钥（推荐）
```

## 🔒 代码保护说明

### PyArmor 混淆

- 将Python代码编译为中间字节码
- 使用混淆算法保护代码逻辑
- 防止简单的反编译

### PyInstaller 打包

- 将所有Python代码和依赖库打包成单个EXE
- 代码不会以明文形式暴露
- 删除源代码后完全隐藏实现

### 安全建议

1. **修改默认密码** - 首次登录后修改admin密码
2. **更改JWT密钥** - 修改config.ini中的JWT_SECRET
3. **启用HTTPS** - 在生产环境前配置SSL证书
4. **限制访问** - 使用防火墙限制IP访问
5. **定期备份** - 备份data/目录

## 🐛 故障排除

### 无法启动应用

```bash
# 检查端口是否被占用
netstat -ano | findstr :3000

# 查看详细错误
# 在start.bat所在目录运行：
iptv-server-3.1.0.exe --debug
```

### 数据库错误

```bash
# 检查data/目录权限
# 确保应用有读写权限

# 如需重置数据库，删除：
data/iptv.db

# 重启应用会自动重建数据库
```

### 性能优化

```bash
# 服务器配置建议
- CPU: 2核心以上
- 内存: 2GB以上
- 硬盘: SSD 50GB以上
```

## 📊 监控和维护

### 查看日志

```bash
# 查看实时日志
type logs/iptv-system.log

# 持续监视日志
PowerShell Get-Content logs/iptv-system.log -Wait
```

### 定期维护

- 每周检查一次日志
- 每月备份一次数据
- 定期检查硬盘空间
- 更新依赖库

## ✅ 验证部署

```bash
# 检查服务是否正常运行
curl http://localhost:3000/api/auth/verify

# 预期返回
# {"error": "未授权，请先登录"}

# 如果返回此错误，说明服务正常运行
```

## 🔄 更新和回滚

### 更新应用

1. 备份现有的 `data/` 目录
2. 重新运行 `build_release.py` 生成新版本
3. 停止旧服务
4. 替换可执行文件
5. 启动新服务

### 回滚数据

```bash
# 如果需要回滚，恢复之前备份的data/目录
# 重启应用即可
```

## 📞 技术支持

遇到问题？检查以下内容：

1. 查看 `logs/` 目录中的错误日志
2. 确认防火墙配置
3. 检查数据库文件权限
4. 验证端口可用性

---

**部署完成！** 🎉

现在您的IPTV管理系统已经可以在生产环境中运行了。

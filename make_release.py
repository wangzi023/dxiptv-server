#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IPTV系统 - 源代码部署包生成脚本

由于PyInstaller与Python 3.10的兼容性问题，改为发布源代码包
用户可以直接运行 start.bat (Windows) 或 ./start.sh (Linux)
"""

import os
import shutil
import zipfile
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
RELEASE_DIR = PROJECT_DIR / 'release'

def create_source_package():
    """创建源代码发布包"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + f" IPTV v3.1.0 - 源代码发布包".center(58) + "║")
    print("╚" + "=" * 58 + "╝")
    
    # 创建release目录
    if RELEASE_DIR.exists():
        shutil.rmtree(RELEASE_DIR)
    RELEASE_DIR.mkdir(parents=True)
    
    print("\n创建发布包...")
    print("=" * 60)
    
    # 复制必要的文件和目录
    include_items = [
        'app',
        'public',
        'data',
        'app_new.py',
        'config.py',
        'requirements.txt',
        'start.sh',
        'README_FINAL.md',
    ]
    
    # Windows批处理
    start_bat_content = """@echo off
chcp 65001 >nul
cd /d "%~dp0"
title IPTV Server v3.1.0

echo.
echo ========================================================
echo   IPTV v3.1.0 - Server Starting...
echo ========================================================
echo.

REM 检查Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python 3.7+ and add to PATH
    pause
    exit /b 1
)

echo [OK] Python environment verified

REM 检查依赖
echo Checking dependencies...
pip show flask >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM 启动应用
echo.
echo Starting IPTV Server...
echo.
python app_new.py

pause
"""
    
    # Linux shell脚本
    start_sh_content = """#!/bin/bash

# IPTV Server v3.1.0 启动脚本

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

APP_NAME="iptv-server"
LOG_FILE="logs/app.log"
PID_FILE="run/$APP_NAME.pid"

mkdir -p logs run

case "$1" in
    start)
        echo "Starting $APP_NAME..."
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if kill -0 "$PID" 2>/dev/null; then
                echo "$APP_NAME is already running (PID: $PID)"
                exit 1
            fi
        fi
        
        # 检查依赖
        pip show flask >/dev/null 2>&1
        if [ $? -ne 0 ]; then
            echo "Installing dependencies..."
            pip install -r requirements.txt
        fi
        
        # 后台启动
        nohup python app_new.py > "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        echo "$APP_NAME started (PID: $!)"
        echo "Logs: $LOG_FILE"
        ;;
    
    stop)
        echo "Stopping $APP_NAME..."
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            kill "$PID" 2>/dev/null
            rm -f "$PID_FILE"
            echo "$APP_NAME stopped"
        else
            echo "$APP_NAME is not running"
        fi
        ;;
    
    restart)
        $0 stop
        sleep 1
        $0 start
        ;;
    
    status)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if kill -0 "$PID" 2>/dev/null; then
                echo "$APP_NAME is running (PID: $PID)"
            else
                echo "$APP_NAME is not running (PID file exists but process gone)"
                rm -f "$PID_FILE"
            fi
        else
            echo "$APP_NAME is not running"
        fi
        ;;
    
    logs)
        echo "Displaying logs..."
        tail -f "$LOG_FILE"
        ;;
    
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
"""
    
    # 复制文件
    for item in include_items:
        src = PROJECT_DIR / item
        dst = RELEASE_DIR / item
        
        if src.exists():
            if src.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__', '.git'))
                print(f"✅ 复制目录: {item}/")
            else:
                shutil.copy2(src, dst)
                print(f"✅ 复制文件: {item}")
    
    # 创建启动脚本
    (RELEASE_DIR / 'start.bat').write_text(start_bat_content, encoding='utf-8')
    print("✅ 创建启动脚本: start.bat")
    
    (RELEASE_DIR / 'start.sh').write_text(start_sh_content, encoding='utf-8')
    os.chmod(RELEASE_DIR / 'start.sh', 0o755)
    print("✅ 创建启动脚本: start.sh")
    
    # 创建README
    readme = RELEASE_DIR / 'DEPLOY_GUIDE.txt'
    readme.write_text("""IPTV系统 v3.1.0 - 部署指南

========================================================

快速开始：

Windows:
  1. 双击 start.bat
  2. 等待依赖安装完成
  3. 访问 http://localhost:3000

Linux:
  1. chmod +x start.sh
  2. ./start.sh start
  3. 访问 http://localhost:3000
     或 http://<服务器IP>:3000

登录凭证：
  用户名: admin
  密码: admin123

系统要求：
  - Python 3.7+ (3.10推荐)
  - pip 包管理器
  - 150MB+ 磁盘空间

依赖包会在首次启动时自动安装。
查看requirements.txt了解详细的依赖列表。

========================================================

故障排除：

Q: Python not found?
A: 请安装Python 3.7+并添加到PATH
   https://www.python.org/

Q: 依赖安装失败？
A: 手动运行: pip install -r requirements.txt

Q: 端口3000被占用？
A: 编辑config.py，修改IPTV_PORT值

Q: Linux下权限不足？
A: 运行: chmod a+x start.sh

========================================================
""", encoding='utf-8')
    print("✅ 创建部署指南: DEPLOY_GUIDE.txt")
    
    # 创建打包完成信息
    print("\n" + "=" * 60)
    print("✅ 发布包创建完成！")
    print("\n发布包位置: release/")
    print("\n包含文件:")
    for item in (RELEASE_DIR / '').rglob('*'):
        if item.is_file():
            size = item.stat().st_size
            if size > 1024*1024:
                size_str = f"{size/(1024*1024):.2f} MB"
            elif size > 1024:
                size_str = f"{size/1024:.2f} KB"
            else:
                size_str = f"{size} B"
            rel_path = item.relative_to(RELEASE_DIR)
            print(f"  - {rel_path} ({size_str})")
    
    print("\n部署步骤:")
    print("  1. 将release/目录复制到服务器")
    print("  2. 在服务器上运行 start.bat (Windows) 或 ./start.sh start (Linux)")
    print("  3. 访问 http://服务器IP:3000")
    print("\n")
    return True

if __name__ == '__main__':
    import sys
    try:
        success = create_source_package()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)
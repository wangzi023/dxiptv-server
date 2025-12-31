#!/bin/bash
# IPTV Server Linux启动脚本

APP_NAME="iptv-server"
APP_VERSION="3.1.0"
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_BIN="$APP_DIR/$APP_NAME-$APP_VERSION"
LOG_FILE="$APP_DIR/logs/iptv-server.log"
PID_FILE="$APP_DIR/iptv-server.pid"

# 创建日志目录
mkdir -p "$APP_DIR/logs"

# 启动应用
start_app() {
    if [ -f "$PID_FILE" ]; then
        old_pid=$(cat "$PID_FILE")
        if kill -0 "$old_pid" 2>/dev/null; then
            echo "应用已在运行 (PID: $old_pid)"
            return 1
        fi
    fi
    
    echo "正在启动 $APP_NAME v$APP_VERSION..."
    
    if [ ! -f "$APP_BIN" ]; then
        echo "❌ 错误: 找不到应用文件 $APP_BIN"
        return 1
    fi
    
    # 后台运行应用
    nohup "$APP_BIN" > "$LOG_FILE" 2>&1 &
    
    # 保存PID
    echo $! > "$PID_FILE"
    
    sleep 2
    
    if kill -0 $! 2>/dev/null; then
        echo "✅ 应用启动成功 (PID: $!)"
        echo "   日志: $LOG_FILE"
        echo "   访问: http://localhost:3000"
        return 0
    else
        echo "❌ 应用启动失败"
        cat "$LOG_FILE"
        return 1
    fi
}

# 停止应用
stop_app() {
    if [ ! -f "$PID_FILE" ]; then
        echo "应用未运行"
        return 0
    fi
    
    pid=$(cat "$PID_FILE")
    
    if kill -0 "$pid" 2>/dev/null; then
        echo "正在停止应用 (PID: $pid)..."
        kill "$pid"
        sleep 2
        
        if kill -0 "$pid" 2>/dev/null; then
            echo "强制停止应用..."
            kill -9 "$pid"
        fi
        
        rm -f "$PID_FILE"
        echo "✅ 应用已停止"
    else
        echo "应用未运行"
        rm -f "$PID_FILE"
    fi
}

# 重启应用
restart_app() {
    stop_app
    sleep 1
    start_app
}

# 查看状态
status_app() {
    if [ ! -f "$PID_FILE" ]; then
        echo "应用未运行"
        return 1
    fi
    
    pid=$(cat "$PID_FILE")
    
    if kill -0 "$pid" 2>/dev/null; then
        echo "应用运行中 (PID: $pid)"
        return 0
    else
        echo "应用未运行 (PID文件: $PID_FILE)"
        return 1
    fi
}

# 查看日志
view_logs() {
    if [ ! -f "$LOG_FILE" ]; then
        echo "日志文件不存在: $LOG_FILE"
        return 1
    fi
    
    tail -f "$LOG_FILE"
}

# 主函数
case "$1" in
    start)
        start_app
        ;;
    stop)
        stop_app
        ;;
    restart)
        restart_app
        ;;
    status)
        status_app
        ;;
    logs)
        view_logs
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "命令说明:"
        echo "  start   - 启动应用"
        echo "  stop    - 停止应用"
        echo "  restart - 重启应用"
        echo "  status  - 查看应用状态"
        echo "  logs    - 查看实时日志"
        exit 1
        ;;
esac

exit $?

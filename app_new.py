"""
IPTV 后台管理系统 - 主入口文件

使用:
    python app.py                    # 开发模式
    python app.py --production       # 生产模式
"""
import os
import sys
import argparse
from app import create_app
from app.utils import get_logger


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='IPTV 后台管理系统')
    parser.add_argument(
        '--production',
        action='store_true',
        help='以生产环境运行'
    )
    parser.add_argument(
        '--testing',
        action='store_true',
        help='以测试环境运行'
    )
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='监听主机地址，默认 0.0.0.0'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=3000,
        help='监听端口，默认 3000'
    )
    
    args = parser.parse_args()
    
    # 确定配置环境
    if args.production:
        config_name = 'production'
    elif args.testing:
        config_name = 'testing'
    else:
        config_name = 'development'
    
    # 设置环境变量
    os.environ['FLASK_ENV'] = config_name
    
    # 创建应用
    app = create_app(config_name)
    logger = get_logger()
    
    # 输出启动信息
    logger.info(f'应用启动在 http://{args.host}:{args.port}')
    logger.info(f'按 Ctrl+C 停止服务器')
    
    # 运行应用
    try:
        app.run(
            host=args.host,
            port=args.port,
            debug=(config_name == 'development')
        )
    except KeyboardInterrupt:
        logger.info('应用已停止')
        sys.exit(0)


if __name__ == '__main__':
    main()

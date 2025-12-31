"""
工程化项目验证脚本
验证所有模块是否按预期工作
"""
import os
import sys
import json

# 添加项目目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_section(title):
    """打印章节标题"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_result(test_name, success, message=""):
    """打印测试结果"""
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"  {status}: {test_name}")
    if message:
        print(f"         {message}")

def test_imports():
    """测试所有模块导入"""
    print_section("1. 测试模块导入")
    
    tests = [
        ("Config", lambda: __import__('config')),
        ("Factory", lambda: __import__('app.factory', fromlist=['create_app'])),
        ("Auth Utils", lambda: __import__('app.utils.auth', fromlist=['hash_password'])),
        ("Database Utils", lambda: __import__('app.utils.database', fromlist=['get_db_context'])),
        ("Logger Utils", lambda: __import__('app.utils.logger', fromlist=['setup_logger'])),
        ("User Service", lambda: __import__('app.services.user_service', fromlist=['UserService'])),
        ("Admin Service", lambda: __import__('app.services.user_service', fromlist=['AdminService'])),
        ("Auth Routes", lambda: __import__('app.routes.auth', fromlist=['auth_bp'])),
        ("Admin Routes", lambda: __import__('app.routes.admin', fromlist=['admin_bp'])),
        ("Database Models", lambda: __import__('app.models.database', fromlist=['init_database'])),
    ]
    
    all_passed = True
    for test_name, test_func in tests:
        try:
            test_func()
            print_result(test_name, True)
        except Exception as e:
            print_result(test_name, False, str(e))
            all_passed = False
    
    return all_passed

def test_config():
    """测试配置系统"""
    print_section("2. 测试配置系统")
    
    try:
        from config import get_config, Config, DevelopmentConfig, ProductionConfig, TestingConfig
        
        # 测试获取默认配置（返回的是类，不是实例）
        dev_config_class = get_config('development')
        dev_config_ok = dev_config_class is DevelopmentConfig
        print_result("获取开发配置", dev_config_ok)
        
        # 测试配置属性
        required_attrs = [
            'SECRET_KEY', 'DATABASE_PATH', 'JWT_SECRET', 
            'JWT_ALGORITHM', 'JWT_EXPIRATION_DAYS',
            'DEFAULT_ADMIN_USERNAME', 'DEFAULT_ADMIN_PASSWORD'
        ]
        
        all_attrs_exist = all(hasattr(dev_config_class, attr) for attr in required_attrs)
        print_result("配置属性检查", all_attrs_exist)
        
        # 测试三种环境
        prod_config_class = get_config('production')
        test_config_class = get_config('testing')
        
        configs_ok = (
            dev_config_class is DevelopmentConfig and dev_config_class.DEBUG and not dev_config_class.TESTING and
            prod_config_class is ProductionConfig and not prod_config_class.DEBUG and not prod_config_class.TESTING and
            test_config_class is TestingConfig and test_config_class.TESTING
        )
        
        print_result("三种环境配置", configs_ok)
        
        return dev_config_ok and all_attrs_exist and configs_ok
        
    except Exception as e:
        print_result("配置系统", False, str(e))
        return False

def test_auth_utils():
    """测试认证工具"""
    print_section("3. 测试认证工具")
    
    try:
        from app.utils.auth import hash_password, verify_password, generate_token, verify_token
        
        # 测试密码哈希
        password = "test_password_123"
        hashed = hash_password(password)
        verify_result = verify_password(password, hashed)
        print_result("密码哈希验证", verify_result)
        
        # 测试错误密码
        wrong_verify = not verify_password("wrong_password", hashed)
        print_result("错误密码拒绝", wrong_verify)
        
        # 测试令牌生成和验证
        token = generate_token(1, "admin", expires_in=7)
        payload = verify_token(token)
        token_valid = payload is not None and payload.get('user_id') == 1
        print_result("令牌生成与验证", token_valid)
        
        # 测试过期令牌
        expired_token = generate_token(1, "admin", expires_in=0)
        import time
        time.sleep(1)
        expired_payload = verify_token(expired_token)
        expired_detected = expired_payload is None
        print_result("过期令牌检测", expired_detected)
        
        return verify_result and wrong_verify and token_valid and expired_detected
        
    except Exception as e:
        print_result("认证工具", False, str(e))
        return False

def test_database_utils():
    """测试数据库工具"""
    print_section("4. 测试数据库工具")
    
    try:
        from app.utils.database import get_db_context, execute_query
        
        # 测试数据库连接
        try:
            with get_db_context() as db:
                cursor = db.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                connection_ok = result is not None
        except Exception as e:
            connection_ok = False
            print(f"         连接错误: {e}")
        
        print_result("数据库连接", connection_ok)
        
        # 测试查询执行
        try:
            result = execute_query("SELECT name FROM sqlite_master WHERE type='table'", fetch_one=False)
            query_ok = result is not None and isinstance(result, list)
        except Exception as e:
            query_ok = False
            print(f"         查询错误: {e}")
        
        print_result("查询执行", query_ok)
        
        return connection_ok and query_ok
        
    except Exception as e:
        print_result("数据库工具", False, str(e))
        return False

def test_database_models():
    """测试数据库模型"""
    print_section("5. 测试数据库模型")
    
    try:
        from app.utils.database import get_db_context
        
        # 检查表是否存在
        with get_db_context() as db:
            cursor = db.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['users', 'accounts', 'sources', 'channels']
        all_tables_exist = all(table in tables for table in required_tables)
        print_result("所有表存在", all_tables_exist)
        
        # 检查默认管理员
        with get_db_context() as db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM users WHERE username = 'admin'")
            admin = cursor.fetchone()
        
        admin_exists = admin is not None
        print_result("默认管理员存在", admin_exists)
        
        if admin:
            print(f"         Admin ID: {admin['id']}")
        
        return all_tables_exist and admin_exists
        
    except Exception as e:
        print_result("数据库模型", False, str(e))
        return False

def test_services():
    """测试服务层"""
    print_section("6. 测试服务层")
    
    try:
        from app.services.user_service import UserService, AdminService
        
        # 测试用户认证
        try:
            result = UserService.authenticate("admin", "adminadmin")
            auth_ok = result is not None and isinstance(result, dict) and result.get('token') is not None
        except Exception as e:
            auth_ok = False
            print(f"         认证错误: {e}")
        
        print_result("用户认证", auth_ok)
        
        # 测试管理员检查
        try:
            is_default = AdminService.is_default_admin(1)
            admin_check_ok = isinstance(is_default, bool)
        except Exception as e:
            admin_check_ok = False
            print(f"         管理员检查错误: {e}")
        
        print_result("默认管理员检查", admin_check_ok)
        
        # 测试获取所有管理员
        try:
            admins = AdminService.get_all_admins()
            get_admins_ok = isinstance(admins, list) and len(admins) > 0
        except Exception as e:
            get_admins_ok = False
            print(f"         获取管理员错误: {e}")
        
        print_result("获取管理员列表", get_admins_ok)
        
        return auth_ok and admin_check_ok and get_admins_ok
        
    except Exception as e:
        print_result("服务层", False, str(e))
        return False

def test_app_factory():
    """测试应用工厂"""
    print_section("7. 测试应用工厂")
    
    try:
        from app.factory import create_app
        
        # 创建应用
        app = create_app('development')
        print_result("应用创建", app is not None)
        
        # 检查蓝图注册
        blueprints_registered = len(app.blueprints) > 0
        print_result("蓝图注册", blueprints_registered)
        
        # 检查静态文件路由
        static_ok = app.static_folder is not None
        print_result("静态文件配置", static_ok)
        
        # 检查错误处理器
        error_handlers_ok = len(app.error_handler_spec.get(None, {})) > 0
        print_result("错误处理器", error_handlers_ok)
        
        return app is not None and blueprints_registered and static_ok and error_handlers_ok
        
    except Exception as e:
        print_result("应用工厂", False, str(e))
        return False

def test_api_routes():
    """测试 API 路由"""
    print_section("8. 测试 API 路由")
    
    try:
        from app.factory import create_app
        
        app = create_app('development')
        client = app.test_client()
        
        # 测试登录端点
        login_response = client.post('/api/auth/login', 
            json={'username': 'admin', 'password': 'adminadmin'})
        login_ok = login_response.status_code == 200
        print_result("登录端点", login_ok)
        
        # 获取令牌
        if login_ok:
            data = login_response.get_json()
            token = data.get('token')
            
            # 测试令牌验证端点
            verify_response = client.get('/api/auth/verify',
                headers={'Authorization': f'Bearer {token}'})
            verify_ok = verify_response.status_code == 200
            print_result("令牌验证端点", verify_ok)
            
            # 测试获取管理员列表
            admins_response = client.get('/api/admins',
                headers={'Authorization': f'Bearer {token}'})
            admins_ok = admins_response.status_code == 200
            print_result("获取管理员端点", admins_ok)
            
            return login_ok and verify_ok and admins_ok
        else:
            print(f"         登录失败: {login_response.get_json()}")
            return False
        
    except Exception as e:
        print_result("API 路由", False, str(e))
        return False

def main():
    """主函数"""
    print("\n" + "█"*60)
    print("█" + " "*58 + "█")
    print("█" + "  🚀 DXIPTV 工程化项目验证脚本".center(58) + "█")
    print("█" + " "*58 + "█")
    print("█"*60)
    
    results = {
        "模块导入": test_imports(),
        "配置系统": test_config(),
        "认证工具": test_auth_utils(),
        "数据库工具": test_database_utils(),
        "数据库模型": test_database_models(),
        "服务层": test_services(),
        "应用工厂": test_app_factory(),
        "API 路由": test_api_routes(),
    }
    
    # 总结
    print_section("验证总结")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✓" if result else "✗"
        print(f"  {status} {name}")
    
    print("\n" + "-"*60)
    print(f"  总体: {passed}/{total} 个测试通过")
    print("-"*60)
    
    if passed == total:
        print("\n  🎉 所有测试通过！项目工程化成功！\n")
        return 0
    else:
        print(f"\n  ⚠️  有 {total - passed} 个测试失败，请检查上方的错误信息\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
应用完整性检查脚本
用于验证项目中的各项功能是否正常工作
"""

import requests
import sys
import time

BASE_URL = "http://localhost:3000"
API_BASE = f"{BASE_URL}/api"

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name, passed, message=""):
    """打印测试结果"""
    status = f"{Colors.GREEN}✓ 通过{Colors.END}" if passed else f"{Colors.RED}✗ 失败{Colors.END}"
    msg = f" - {message}" if message else ""
    print(f"  {status} {name}{msg}")

def print_section(title):
    """打印章节标题"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}{Colors.END}\n")

def check_server():
    """检查服务器是否运行"""
    print_section("1. 服务器连接检查")
    try:
        response = requests.get(BASE_URL, timeout=5)
        print_test("服务器连接", True, f"HTTP {response.status_code}")
        return True
    except requests.ConnectionError:
        print_test("服务器连接", False, "无法连接到服务器")
        return False
    except Exception as e:
        print_test("服务器连接", False, str(e))
        return False

def check_pages():
    """检查页面是否正常"""
    print_section("2. 页面访问检查")
    
    pages = [
        ("/", "首页"),
        ("/login.html", "登录页"),
        ("/index.html", "首页（直接访问）"),
        ("/admin.html", "管理页"),
    ]
    
    all_passed = True
    for path, name in pages:
        try:
            response = requests.get(f"{BASE_URL}{path}", timeout=5)
            passed = response.status_code == 200
            print_test(name, passed, f"HTTP {response.status_code}")
            all_passed = all_passed and passed
        except Exception as e:
            print_test(name, False, str(e))
            all_passed = False
    
    return all_passed

def check_static_files():
    """检查静态文件"""
    print_section("3. 静态文件检查")
    
    files = [
        ("/app.js", "app.js"),
        ("/login.html", "login.html"),
        ("/index.html", "index.html"),
    ]
    
    all_passed = True
    for path, name in files:
        try:
            response = requests.head(f"{BASE_URL}{path}", timeout=5)
            passed = response.status_code == 200
            print_test(name, passed, f"HTTP {response.status_code}")
            all_passed = all_passed and passed
        except Exception as e:
            print_test(name, False, str(e))
            all_passed = False
    
    return all_passed

def check_api():
    """检查 API 端点"""
    print_section("4. API 端点检查")
    
    all_passed = True
    
    # 1. 测试登录端点
    try:
        response = requests.post(
            f"{API_BASE}/auth/login",
            json={"username": "admin", "password": "adminadmin"},
            timeout=5
        )
        passed = response.status_code == 200
        print_test("登录 POST /api/auth/login", passed, f"HTTP {response.status_code}")
        all_passed = all_passed and passed
    except Exception as e:
        print_test("登录 POST /api/auth/login", False, str(e))
        all_passed = False
    
    # 2. 测试 verify 端点（无认证，应该返回 401）
    try:
        response = requests.get(f"{API_BASE}/auth/verify", timeout=5)
        passed = response.status_code == 401
        print_test("验证 GET /api/auth/verify（无认证）", passed, f"HTTP {response.status_code}")
        all_passed = all_passed and passed
    except Exception as e:
        print_test("验证 GET /api/auth/verify（无认证）", False, str(e))
        all_passed = False
    
    # 3. 测试管理员列表端点（无认证，应该返回 401）
    try:
        response = requests.get(f"{API_BASE}/admins", timeout=5)
        passed = response.status_code == 401
        print_test("管理员列表 GET /api/admins（无认证）", passed, f"HTTP {response.status_code}")
        all_passed = all_passed and passed
    except Exception as e:
        print_test("管理员列表 GET /api/admins（无认证）", False, str(e))
        all_passed = False
    
    return all_passed

def check_auth():
    """检查认证流程"""
    print_section("5. 认证流程检查")
    
    # 测试登录
    try:
        response = requests.post(
            f"{API_BASE}/auth/login",
            json={"username": "admin", "password": "adminadmin"},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            has_token = "token" in data
            has_user = "user" in data
            
            print_test("登录请求", True, f"HTTP {response.status_code}")
            print_test("Token 返回", has_token)
            print_test("用户信息返回", has_user)
            
            if has_token:
                token = data["token"]
                
                # 测试 token 验证
                verify_response = requests.get(
                    f"{API_BASE}/auth/verify",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5
                )
                
                verify_passed = verify_response.status_code == 200
                print_test("Token 验证", verify_passed, f"HTTP {verify_response.status_code}")
                
                return True
            else:
                return False
        else:
            print_test("登录请求", False, f"HTTP {response.status_code}")
            return False
    except Exception as e:
        print_test("认证流程", False, str(e))
        return False

def check_database():
    """检查数据库"""
    print_section("6. 数据库检查")
    
    import os
    db_path = os.path.join("data", "iptv.db")
    
    exists = os.path.exists(db_path)
    print_test("数据库文件", exists, f"{db_path}")
    
    if exists:
        size = os.path.getsize(db_path)
        print_test("数据库大小", True, f"{size} 字节")
    
    return exists

def main():
    """运行所有检查"""
    print(f"\n{Colors.YELLOW}DXIPTV 项目完整性检查{Colors.END}\n")
    print(f"目标服务器: {BASE_URL}")
    print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查列表
    checks = [
        ("服务器连接", check_server),
        ("页面访问", check_pages),
        ("静态文件", check_static_files),
        ("API 端点", check_api),
        ("认证流程", check_auth),
        ("数据库", check_database),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"{Colors.RED}检查 '{name}' 异常: {e}{Colors.END}")
            results[name] = False
    
    # 总结
    print_section("检查总结")
    
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    for name, result in results.items():
        status = f"{Colors.GREEN}✓{Colors.END}" if result else f"{Colors.RED}✗{Colors.END}"
        print(f"  {status} {name}")
    
    print(f"\n总计: {Colors.GREEN}{passed_count}{Colors.END}/{total_count} 项检查通过")
    
    if passed_count == total_count:
        print(f"\n{Colors.GREEN}✓ 所有检查通过！应用运行正常。{Colors.END}\n")
        return 0
    else:
        print(f"\n{Colors.RED}✗ 有 {total_count - passed_count} 项检查失败，请检查应用状态。{Colors.END}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())

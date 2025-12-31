"""
用户服务 - 管理员和用户管理业务逻辑
"""
from app.utils import (
    hash_password, verify_password, get_db_context,
    generate_token, execute_query, execute_update
)
from config import get_config


config = get_config()


class UserService:
    """用户服务类"""
    
    @staticmethod
    def get_user_by_id(user_id):
        """
        根据 ID 获取用户
        
        Args:
            user_id (int): 用户 ID
            
        Returns:
            dict: 用户信息，不存在则返回 None
        """
        return execute_query(
            'SELECT id, username, role, is_default, is_active, is_first_login FROM users WHERE id = ?',
            (user_id,),
            fetch_one=True
        )
    
    @staticmethod
    def get_user_by_username(username):
        """
        根据用户名获取用户
        
        Args:
            username (str): 用户名
            
        Returns:
            dict: 用户信息，不存在则返回 None
        """
        return execute_query(
            'SELECT id, username, password, role, is_default, is_active, is_first_login FROM users WHERE username = ?',
            (username,),
            fetch_one=True
        )
    
    @staticmethod
    def authenticate(username, password):
        """
        验证用户凭证
        
        Args:
            username (str): 用户名
            password (str): 密码
            
        Returns:
            dict: 验证成功返回用户信息（包括令牌），失败返回 None
        """
        user = UserService.get_user_by_username(username)
        
        if not user:
            return None
        
        if not verify_password(password, user['password']):
            return None
        
        # 生成令牌
        token = generate_token(user['id'], user['username'])
        
        return {
            'id': user['id'],
            'username': user['username'],
            'role': user['role'],
            'is_default': user['is_default'],
            'is_first_login': user['is_first_login'],
            'token': token
        }
    
    @staticmethod
    def change_password(user_id, old_password, new_password):
        """
        修改密码
        
        Args:
            user_id (int): 用户 ID
            old_password (str): 旧密码
            new_password (str): 新密码
            
        Returns:
            tuple: (成功标志, 消息)
        """
        # 验证密码长度
        if len(new_password) < config.PASSWORD_MIN_LENGTH:
            return False, f'密码至少需要 {config.PASSWORD_MIN_LENGTH} 位'
        
        if len(new_password) > config.PASSWORD_MAX_LENGTH:
            return False, f'密码最多 {config.PASSWORD_MAX_LENGTH} 位'
        
        # 获取用户当前密码
        user = UserService.get_user_by_id(user_id)
        if not user:
            return False, '用户不存在'
        
        # 验证旧密码
        if not verify_password(old_password, 
                               execute_query(
                                   'SELECT password FROM users WHERE id = ?',
                                   (user_id,),
                                   fetch_one=True
                               )['password']):
            return False, '旧密码错误'
        
        # 更新密码
        new_password_hash = hash_password(new_password)
        execute_update(
            'UPDATE users SET password = ?, is_first_login = 0 WHERE id = ?',
            (new_password_hash, user_id)
        )
        
        return True, '密码修改成功'


class AdminService:
    """管理员服务类"""
    
    @staticmethod
    def is_default_admin(user_id):
        """
        检查用户是否为默认管理员
        
        Args:
            user_id (int): 用户 ID
            
        Returns:
            bool: 是否为默认管理员
        """
        user = execute_query(
            'SELECT is_default FROM users WHERE id = ?',
            (user_id,),
            fetch_one=True
        )
        return user and user['is_default'] == 1
    
    @staticmethod
    def get_all_admins():
        """
        获取所有管理员列表
        
        Returns:
            list: 管理员列表
        """
        return execute_query(
            'SELECT id, username, role, is_default, is_active, created_at FROM users ORDER BY is_default DESC, created_at DESC'
        )
    
    @staticmethod
    def create_admin(username, password):
        """
        创建新管理员
        
        Args:
            username (str): 用户名
            password (str): 密码
            
        Returns:
            tuple: (成功标志, 消息/ID)
        """
        # 验证用户名
        if len(username) < config.USERNAME_MIN_LENGTH:
            return False, f'用户名至少需要 {config.USERNAME_MIN_LENGTH} 位'
        
        if len(username) > config.USERNAME_MAX_LENGTH:
            return False, f'用户名最多 {config.USERNAME_MAX_LENGTH} 位'
        
        # 验证密码
        if len(password) < config.PASSWORD_MIN_LENGTH:
            return False, f'密码至少需要 {config.PASSWORD_MIN_LENGTH} 位'
        
        # 检查用户名是否已存在
        existing = execute_query(
            'SELECT id FROM users WHERE username = ?',
            (username,),
            fetch_one=True
        )
        if existing:
            return False, '用户名已存在'
        
        # 创建管理员
        password_hash = hash_password(password)
        execute_update(
            'INSERT INTO users (username, password, role, is_default, is_active, is_first_login) VALUES (?, ?, ?, ?, ?, ?)',
            (username, password_hash, 'admin', 0, 1, 1)
        )
        
        # 获取新建的管理员 ID
        user = execute_query(
            'SELECT id FROM users WHERE username = ?',
            (username,),
            fetch_one=True
        )
        
        return True, user['id']
    
    @staticmethod
    def update_admin(admin_id, current_user_id, **kwargs):
        """
        更新管理员信息
        
        Args:
            admin_id (int): 目标管理员 ID
            current_user_id (int): 当前用户 ID
            **kwargs: 更新字段 (new_password, is_active)
            
        Returns:
            tuple: (成功标志, 消息)
        """
        # 获取目标管理员
        target_admin = execute_query(
            'SELECT is_default FROM users WHERE id = ?',
            (admin_id,),
            fetch_one=True
        )
        
        if not target_admin:
            return False, '管理员不存在'
        
        # 权限检查
        is_target_default = target_admin['is_default'] == 1
        is_current_default = AdminService.is_default_admin(current_user_id)
        
        # 修改他人时需要是默认管理员
        if current_user_id != admin_id and not is_current_default:
            return False, '只有默认管理员可以修改其他管理员'
        
        # 默认管理员不能被修改（除了密码）
        if is_target_default and current_user_id != admin_id and 'is_active' in kwargs:
            return False, '无法修改默认管理员的状态'
        
        # 修改密码
        if 'new_password' in kwargs:
            new_password = kwargs['new_password']
            
            if len(new_password) < config.PASSWORD_MIN_LENGTH:
                return False, f'密码至少需要 {config.PASSWORD_MIN_LENGTH} 位'
            
            # 修改自己的密码需要验证旧密码
            if current_user_id == admin_id:
                old_password = kwargs.get('old_password')
                if not old_password:
                    return False, '修改自己的密码需要提供旧密码'
                
                current_password = execute_query(
                    'SELECT password FROM users WHERE id = ?',
                    (admin_id,),
                    fetch_one=True
                )
                if not verify_password(old_password, current_password['password']):
                    return False, '旧密码错误'
            
            new_password_hash = hash_password(new_password)
            execute_update(
                'UPDATE users SET password = ? WHERE id = ?',
                (new_password_hash, admin_id)
            )
        
        # 修改状态
        if 'is_active' in kwargs and current_user_id != admin_id:
            if is_target_default:
                return False, '无法修改默认管理员'
            
            is_active = 1 if kwargs['is_active'] else 0
            execute_update(
                'UPDATE users SET is_active = ? WHERE id = ?',
                (is_active, admin_id)
            )
        
        return True, '管理员信息更新成功'
    
    @staticmethod
    def delete_admin(admin_id):
        """
        删除管理员
        
        Args:
            admin_id (int): 管理员 ID
            
        Returns:
            tuple: (成功标志, 消息)
        """
        # 获取目标管理员
        target = execute_query(
            'SELECT is_default FROM users WHERE id = ?',
            (admin_id,),
            fetch_one=True
        )
        
        if not target:
            return False, '管理员不存在'
        
        if target['is_default'] == 1:
            return False, '无法删除默认管理员'
        
        # 删除管理员
        execute_update('DELETE FROM users WHERE id = ?', (admin_id,))
        
        return True, '管理员删除成功'

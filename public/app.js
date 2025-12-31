const API_BASE_URL = `${window.location.origin}/api`;

// ==================== 认证管理 ====================

// 获取认证令牌
function getAuthToken() {
  return localStorage.getItem('auth_token');
}

// 设置API请求头
function getAuthHeaders() {
  const token = getAuthToken();
  return {
    'Content-Type': 'application/json',
    'Authorization': token ? `Bearer ${token}` : ''
  };
}

// 检查认证
async function checkAuth() {
  const token = getAuthToken();
  if (!token) {
    // 没有 token，重定向到登录页
    window.location.href = '/login.html';
    return false;
  }
  
  // 验证令牌有效性
  try {
    const response = await fetch(`${API_BASE_URL}/auth/verify`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    const data = await response.json();
    
    if (data.error) {
      // Token 无效或过期
      logout();
      return false;
    } else {
      // Token 有效，显示用户名
      if (data.user && data.user.username) {
        currentUser = data.user;
        isDefaultAdmin = data.user.is_default === 1;
        const usernameEl = document.getElementById('username');
        if (usernameEl) {
          usernameEl.textContent = data.user.username;
        }
      }
      
      // 隐藏加载屏幕
      const loadingScreen = document.getElementById('loadingScreen');
      if (loadingScreen) {
        loadingScreen.style.display = 'none';
      }
      
      return true;
    }
  } catch (error) {
    // 请求失败，可能是网络问题，但仍然登出
    console.error('验证 token 失败:', error);
    logout();
    return false;
  }
}

// 登出
async function logout() {
  const token = getAuthToken();
  if (token) {
    try {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: 'POST',
        headers: getAuthHeaders()
      });
    } catch (error) {
      console.warn('记录登出日志失败', error);
    }
  }
  localStorage.removeItem('auth_token');
  window.location.href = '/login.html';
}

// 日志筛选状态
const logsState = {
  type: '',
  level: '',
  status: '',
  keyword: '',
  page: 1,
  pageSize: 10,
  total: 0
};

// 仪表盘日志轮询状态
let dashboardLogPollingIntervals = {
  system: null,
  operation: null,
  task: null
};
const DASHBOARD_LOG_POLL_INTERVAL = 5000; // 5秒轮询一次
const DASHBOARD_LOG_PAGE_SIZE = 30; // 获取最新30条

// 页面加载时检查认证
document.addEventListener('DOMContentLoaded', () => {
  checkAuth();
});

// 页面切换
function showPage(pageName) {
  // 离开仪表盘时停止轮询
  if (document.getElementById('dashboard-page').style.display !== 'none') {
    stopDashboardLogPolling();
  }
  
  // 隐藏所有页面
  document.querySelectorAll('.page-content').forEach(page => {
    page.style.display = 'none';
  });
  
  // 移除所有active类
  document.querySelectorAll('.sidebar .nav-link').forEach(link => {
    link.classList.remove('active');
  });
  
  // 显示目标页面
  document.getElementById(pageName + '-page').style.display = 'block';
  
  // 添加active类到当前导航
  event.target.closest('.nav-link').classList.add('active');
  
  // 加载相应数据
  switch(pageName) {
    case 'dashboard':
      loadDashboard();
      break;
    case 'accounts':
      loadAccounts();
      break;
    case 'sources':
      loadSources();
      break;
    case 'channels':
      loadAccountsForChannelFilter();
      loadCategoriesForChannelFilter();
      loadChannelTemplates();
      loadChannels();
      break;
    case 'templates':
      loadTemplateGroups();
      loadTemplateStatistics();
      loadTemplates();
      break;
    case 'admin':
      loadAdmins();
      break;
    case 'schedule':
      loadScheduleTasks();
      break;
    case 'logs':
      loadLogsPage();
      break;
  }
}

// 加载仪表盘数据
// 计算日志容器的动态高度
function calculateLogContainerHeight() {
  const viewportHeight = window.innerHeight;
  const headerHeight = 60; // 顶部导航
  const dashboardPaddingTop = 20;
  const cardHeaderHeight = 48; // 卡片头部
  const cardPaddingBottom = 15;
  const minHeight = 250; // 最小高度
  const maxHeight = 600; // 最大高度
  
  const availableHeight = viewportHeight - headerHeight - dashboardPaddingTop - cardHeaderHeight - cardPaddingBottom;
  const calculatedHeight = Math.max(minHeight, Math.min(availableHeight, maxHeight));
  
  document.documentElement.style.setProperty('--log-container-height', `${calculatedHeight}px`);
}

// 在窗口resize时重新计算高度
window.addEventListener('resize', () => {
  calculateLogContainerHeight();
});

async function loadDashboard() {
  try {
    // 计算日志容器高度
    calculateLogContainerHeight();
    
    const response = await fetch(`${API_BASE_URL}/stats`, {
      headers: getAuthHeaders()
    });
    const data = await response.json();
    
    if (data) {
      document.getElementById('total-accounts').textContent = data.total_accounts || 0;
      document.getElementById('total-sources').textContent = data.total_sources || 0;
      document.getElementById('total-channels').textContent = data.total_channels || 0;
      document.getElementById('active-accounts').textContent = data.active_accounts || 0;
    }
    
    // 加载定时任务统计
    try {
      const tasksResponse = await fetch(`${API_BASE_URL}/schedule/tasks`, {
        headers: getAuthHeaders()
      });
      const tasksData = await tasksResponse.json();
      const tasks = tasksData.tasks || [];
      const activeTasks = tasks.filter(task => task.is_enabled === 1 || task.is_enabled === true);
      
      document.getElementById('total-tasks').textContent = tasks.length;
      document.getElementById('active-tasks').textContent = activeTasks.length;
    } catch (taskError) {
      console.error('加载定时任务统计失败:', taskError);
      document.getElementById('total-tasks').textContent = '0';
      document.getElementById('active-tasks').textContent = '0';
    }
    
    // 加载日志及启动轮询
    loadSystemLogs();
    loadOperationLogs();
    loadTaskLogs();
    startDashboardLogPolling();
  } catch (error) {
    console.error('加载仪表盘数据失败:', error);
    showAlert('加载数据失败', 'danger');
  }
}

// 加载账户列表
async function loadAccounts() {
  try {
    const response = await fetch(`${API_BASE_URL}/accounts`, {
      headers: getAuthHeaders()
    });
    const data = await response.json();
    
    const tbody = document.getElementById('accounts-table-body');
    tbody.innerHTML = '';
    
    if (data.data.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">暂无数据</td></tr>';
      return;
    }
    
    data.data.forEach(account => {
      const isActive = String(account.status) === '0';
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${account.id}</td>
        <td>${account.username}</td>
        <td>${account.mac}</td>
        <td>${account.imei || '-'}</td>
        <td><span class="status-${isActive ? 'active' : 'inactive'}">${isActive ? '启用' : '停用'}</span></td>
        <td>${new Date(account.created_at).toLocaleString()}</td>
        <td>
          <button class="btn btn-sm btn-outline-primary" onclick="editAccount(${account.id})">
            <i class="bi bi-pencil"></i>
          </button>
          <button class="btn btn-sm btn-outline-danger" onclick="deleteAccount(${account.id})">
            <i class="bi bi-trash"></i>
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });
    
    // 更新账户选择器
    updateAccountSelectors(data.data);
  } catch (error) {
    console.error('加载账户列表失败:', error);
    showAlert('加载账户列表失败', 'danger');
  }
}

// 更新账户选择器
function updateAccountSelectors(accounts) {
  const selectors = [
    document.getElementById('source-account-select'),
    document.getElementById('account-filter')
  ];
  
  selectors.forEach(select => {
    if (!select) return;
    
    // 保留第一个默认选项
    const defaultOption = select.options[0];
    select.innerHTML = '';
    select.appendChild(defaultOption);
    
    accounts.forEach(account => {
      const option = document.createElement('option');
      option.value = account.id;
      option.textContent = account.username;
      select.appendChild(option);
    });
  });
}

// 显示添加账户模态框
function showAddAccountModal() {
  const modal = new bootstrap.Modal(document.getElementById('addAccountModal'));
  document.getElementById('addAccountForm').reset();
  modal.show();
}

// 添加账户
async function addAccount() {
  const form = document.getElementById('addAccountForm');
  const formData = new FormData(form);
  const data = Object.fromEntries(formData);
  
  try {
    const response = await fetch(`${API_BASE_URL}/accounts`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data)
    });
    
    const result = await response.json();
    
    if (response.ok) {
      showAlert('账户添加成功', 'success');
      bootstrap.Modal.getInstance(document.getElementById('addAccountModal')).hide();
      loadAccounts();
    } else {
      if (response.status === 401) {
        logout();
      } else {
        showAlert(result.error || '添加失败', 'danger');
      }
    }
  } catch (error) {
    console.error('添加账户失败:', error);
    showAlert('添加账户失败', 'danger');
  }
}

// 编辑账户
async function editAccount(id) {
  try {
    // 获取账户详情
    const response = await fetch(`${API_BASE_URL}/accounts/${id}`, {
      headers: getAuthHeaders()
    });
    
    const result = await response.json();
    
    if (!response.ok) {
      showAlert(result.error || '获取账户信息失败', 'danger');
      return;
    }
    
    const account = result.data;
    
    if (!account || !account.id) {
      showAlert('账户数据无效', 'danger');
      console.error('账户数据:', account);
      return;
    }
    
    // 存储正在编辑的账户ID到全局变量
    editingAccountId = account.id;
    
    // 填充表单
    document.getElementById('accountId').value = account.id;
    document.getElementById('accountUsername').value = account.username || '';
    document.getElementById('accountPassword').value = account.password || ''; // 显示实际密码
    document.getElementById('accountMac').value = account.mac || '';
    document.getElementById('accountImei').value = account.imei || '';
    document.getElementById('accountAddress').value = account.address || '';
    document.getElementById('accountRemark').value = account.remark || '';
    document.getElementById('accountStatus').value = String(account.status ?? 0);
    
    console.log('编辑账户 ID:', editingAccountId, '表单ID:', document.getElementById('accountId').value); // 调试
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('editAccountModal'));
    modal.show();
  } catch (error) {
    console.error('获取账户信息失败:', error);
    showAlert('获取账户信息失败', 'danger');
  }
}

// 保存编辑的账户
async function saveEditAccount(event) {
  if (event) {
    event.preventDefault();
  }
  
  // 优先使用全局变量，如果没有则尝试从表单获取
  const accountId = editingAccountId || document.getElementById('accountId').value;
  
  console.log('保存账户, 全局ID:', editingAccountId, '表单ID:', document.getElementById('accountId').value); // 调试信息
  
  if (!accountId) {
    showAlert('账户ID无效', 'danger');
    console.error('accountId为空');
    return;
  }
  
  const username = document.getElementById('accountUsername').value.trim();
  const password = document.getElementById('accountPassword').value.trim();
  const mac = document.getElementById('accountMac').value.trim();
  const imei = document.getElementById('accountImei').value.trim();
  const address = document.getElementById('accountAddress').value.trim();
  const remark = document.getElementById('accountRemark').value.trim();
  const status = Number(document.getElementById('accountStatus').value);
  
  if (!username || !mac) {
    showAlert('用户名和MAC地址不能为空', 'warning');
    return;
  }
  
  // 构建请求数据
  const updateData = {
    username,
    mac,
    imei: imei || null,
    address: address || null,
    remark: remark || null,
    status
  };
  
  // 只有输入了新密码才更新密码
  if (password) {
    updateData.password = password;
  }
  
  try {
    const response = await fetch(`${API_BASE_URL}/accounts/${accountId}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(updateData)
    });
    
    const result = await response.json();
    
    if (response.ok) {
      showAlert('账户更新成功', 'success');
      editingAccountId = null; // 清除全局变量
      bootstrap.Modal.getInstance(document.getElementById('editAccountModal')).hide();
      loadAccounts();
    } else {
      if (response.status === 401) {
        logout();
      } else {
        showAlert(result.error || '更新失败', 'danger');
      }
    }
  } catch (error) {
    console.error('更新账户失败:', error);
    showAlert('更新账户失败', 'danger');
  }
}

// 删除账户
async function deleteAccount(id) {
  if (!confirm('确定要删除这个账户吗?')) return;
  
  try {
    const response = await fetch(`${API_BASE_URL}/accounts/${id}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });
    
    const result = await response.json();
    
    if (response.ok) {
      showAlert('账户删除成功', 'success');
      loadAccounts();
    } else {
      if (response.status === 401) {
        logout();
      } else {
        showAlert(result.error || '删除失败', 'danger');
      }
    }
  } catch (error) {
    console.error('删除账户失败:', error);
    showAlert('删除账户失败', 'danger');
  }
}

// 加载源列表
async function loadSources() {
  try {
    const response = await fetch(`${API_BASE_URL}/sources`, {
      headers: getAuthHeaders()
    });
    const data = await response.json();
    
    const tbody = document.getElementById('sources-table-body');
    tbody.innerHTML = '';
    
    if (data.data.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">暂无数据</td></tr>';
      return;
    }
    
    data.data.forEach(source => {
      const isActive = String(source.status) === '0';
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${source.id}</td>
        <td>${source.name}</td>
        <td>${source.account_name || '-'}</td>
        <td>${source.channel_count || 0}</td>
        <td>${source.last_updated ? new Date(source.last_updated).toLocaleString() : '-'}</td>
        <td><span class="status-${isActive ? 'active' : 'inactive'}">${isActive ? '启用' : '停用'}</span></td>
        <td>
          <button class="btn btn-sm btn-outline-danger" onclick="deleteSource(${source.id})">
            <i class="bi bi-trash"></i>
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (error) {
    console.error('加载源列表失败:', error);
    showAlert('加载源列表失败', 'danger');
  }
}

// 显示获取源模态框
async function showFetchSourceModal() {
  // 先加载账户列表
  try {
    const response = await fetch(`${API_BASE_URL}/accounts`, {
      headers: getAuthHeaders()
    });
    const data = await response.json();
    updateAccountSelectors(data.data);
  } catch (error) {
    console.error('加载账户列表失败:', error);
  }
  
  const modal = new bootstrap.Modal(document.getElementById('fetchSourceModal'));
  document.getElementById('fetchSourceForm').reset();
  modal.show();
}

// 获取源
async function fetchSource() {
  const form = document.getElementById('fetchSourceForm');
  const formData = new FormData(form);
  const data = Object.fromEntries(formData);
  
  if (!data.account_id) {
    showAlert('请选择账户', 'warning');
    return;
  }
  
  const button = event.target;
  button.disabled = true;
  button.innerHTML = '<span class="spinner-border spinner-border-sm"></span> 正在获取...';
  
  try {
    const response = await fetch(`${API_BASE_URL}/sources/fetch`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data)
    });
    
    const result = await response.json();
    
    if (response.ok) {
      showAlert(`源获取成功! 共 ${result.data.channel_count} 个频道`, 'success');
      bootstrap.Modal.getInstance(document.getElementById('fetchSourceModal')).hide();
      loadSources();
      loadDashboard();
    } else {
      if (response.status === 401) {
        logout();
      } else {
        showAlert(result.error || '获取失败', 'danger');
      }
    }
  } catch (error) {
    console.error('获取源失败:', error);
    showAlert('获取源失败: ' + error.message, 'danger');
  } finally {
    button.disabled = false;
    button.innerHTML = '获取';
  }
}

// 删除源
async function deleteSource(id) {
  if (!confirm('确定要删除这个源吗?')) return;
  
  try {
    const response = await fetch(`${API_BASE_URL}/sources/${id}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });
    
    const result = await response.json();
    
    if (response.ok) {
      showAlert('源删除成功', 'success');
      loadSources();
    } else {
      if (response.status === 401) {
        logout();
      } else {
        showAlert(result.error || '删除失败', 'danger');
      }
    }
  } catch (error) {
    console.error('删除源失败:', error);
    showAlert('删除源失败', 'danger');
  }
}

// 加载频道列表
async function loadChannels() {
  const accountId = document.getElementById('account-filter')?.value || '';
  const category = document.getElementById('category-filter')?.value || '';
  
  let url = `${API_BASE_URL}/channels`;
  const params = [];
  if (accountId) params.push(`account_id=${accountId}`);
  if (params.length > 0) url += '?' + params.join('&');
  
  try {
    const response = await fetch(url, {
      headers: getAuthHeaders()
    });
    const data = await response.json();
    
    const tbody = document.getElementById('channels-table-body');
    tbody.innerHTML = '';
    
    // 前端过滤分类
    let channels = data.data;
    if (category) {
      channels = channels.filter(ch => ch.category === category);
    }
    
    if (channels.length === 0) {
      tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">暂无数据</td></tr>';
      return;
    }
    
    channels.forEach(channel => {
      const isActive = String(channel.status) === '0';
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><input type="checkbox" class="channel-checkbox" data-id="${channel.id}" onchange="updateSelectedChannels()"></td>
        <td>${channel.id}</td>
        <td>${channel.channel_id}</td>
        <td>${channel.channel_name}</td>
        <td>${channel.account_name || '-'}</td>
        <td>${channel.category || '-'}</td>
        <td><span class="status-${isActive ? 'active' : 'inactive'}">${isActive ? '启用' : '停用'}</span></td>
        <td>
          <button class="btn btn-sm btn-outline-danger" onclick="deleteChannel(${channel.id})">
            <i class="bi bi-trash"></i>
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });
    
    // 重置选择
    document.getElementById('select-all-channels').checked = false;
    updateSelectedChannels();
  } catch (error) {
    console.error('加载频道列表失败:', error);
    showAlert('加载频道列表失败', 'danger');
  }
}

// 为频道筛选器加载分类列表
async function loadCategoriesForChannelFilter() {
  try {
    const response = await fetch(`${API_BASE_URL}/channels`, {
      headers: getAuthHeaders()
    });
    
    if (!response.ok) {
      if (response.status === 401) {
        logout();
        return;
      }
      console.error('加载频道列表失败:', response.status);
      return;
    }
    
    const data = await response.json();
    
    // 从频道数据中提取所有唯一的分类
    const categories = new Set();
    data.data.forEach(channel => {
      if (channel.category) {
        categories.add(channel.category);
      }
    });
    
    // 更新分类筛选下拉框
    const categoryFilter = document.getElementById('category-filter');
    if (categoryFilter) {
      categoryFilter.innerHTML = '<option value="">所有分类</option>';
      Array.from(categories).sort().forEach(category => {
        const option = document.createElement('option');
        option.value = category;
        option.textContent = category;
        categoryFilter.appendChild(option);
      });
    }
  } catch (error) {
    console.error('加载分类列表失败:', error);
  }
}

// 为频道筛选器加载账户列表
async function loadAccountsForChannelFilter() {
  try {
    const response = await fetch(`${API_BASE_URL}/accounts`, {
      headers: getAuthHeaders()
    });
    
    if (!response.ok) {
      if (response.status === 401) {
        logout();
        return;
      }
      console.error('加载账户列表失败:', response.status);
      return;
    }
    
    const data = await response.json();
    
    // 更新账户筛选下拉框
    const accountFilter = document.getElementById('account-filter');
    if (accountFilter) {
      accountFilter.innerHTML = '<option value="">所有账户</option>';
      data.data.forEach(account => {
        const option = document.createElement('option');
        option.value = account.id;
        option.textContent = account.username;
        accountFilter.appendChild(option);
      });
    }
  } catch (error) {
    console.error('加载账户列表失败:', error);
  }
}

// 筛选频道
function filterChannels() {
  loadChannels();
}

// 刷新频道
function refreshChannels() {
  loadChannels();
}

// 导出频道文本
async function exportChannels() {
  try {

    // 获取当前筛选条件
    const accountFilter = document.getElementById('account-filter');
    const categoryFilter = document.getElementById('category-filter');
    
    const sourceId = accountFilter && accountFilter.value !== '' ? accountFilter.value : null;
    const category = categoryFilter && categoryFilter.value !== '' ? categoryFilter.value : null;
    
    // 构建查询参数
    const params = new URLSearchParams();
    if (sourceId) {
      params.append('source_id', sourceId);
    }
    if (category) {
      params.append('category', category);
    }
    
    // 构建URL
    const url = `${API_BASE_URL}/iptv/channels/export${params.toString() ? '?' + params.toString() : ''}`;
    
    // 使用fetch下载文件
    const response = await fetch(url, {
      method: 'GET',
      headers: getAuthHeaders()
    });
    
    if (!response.ok) {
      if (response.status === 401) {
        console.error('401错误: 未授权');
        showAlert('登录已过期，请重新登录', 'warning');
        logout();
        return;
      }
      // 尝试解析JSON错误信息
      try {
        const result = await response.json();
        showAlert(result.message || '导出失败', 'danger');
      } catch {
        showAlert(`导出失败 (${response.status})`, 'danger');
      }
      return;
    }
    
    // 获取文件内容
    const blob = await response.blob();
    
    // 创建下载链接
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = downloadUrl;
    
    // 生成文件名
    let filename = 'channels';
    if (category) {
      filename += `_${category}`;
    }
    if (sourceId) {
      const accountName = accountFilter.options[accountFilter.selectedIndex].text;
      filename += `_${accountName}`;
    }
    filename += '.txt';
    
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(downloadUrl);
    
    showAlert('频道列表导出成功', 'success');
    
  } catch (error) {
    console.error('导出频道失败:', error);
    showAlert('导出频道失败', 'danger');
  }
}

// 删除频道
async function deleteChannel(id) {
  if (!confirm('确定要删除这个频道吗?')) return;
  
  try {
    const response = await fetch(`${API_BASE_URL}/channels/${id}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });
    
    const result = await response.json();
    
    if (response.ok) {
      showAlert('频道删除成功', 'success');
      loadChannels();
    } else {
      if (response.status === 401) {
        logout();
      } else {
        showAlert(result.error || '删除失败', 'danger');
      }
    }
  } catch (error) {
    console.error('删除频道失败:', error);
    showAlert('删除频道失败', 'danger');
  }
}

// 启用/停用频道
async function toggleChannel(id, isActive) {
  try {
    const response = await fetch(`${API_BASE_URL}/channels/${id}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify({ status: isActive ? 1 : 0 })
    });
    const result = await response.json();
    if (response.ok) {
      showAlert(isActive ? '频道已停用' : '频道已启用', 'success');
      loadChannels();
    } else {
      showAlert(result.error || '状态更新失败', 'danger');
    }
  } catch (error) {
    console.error('更新频道状态失败:', error);
    showAlert('更新频道状态失败', 'danger');
  }
}

// 编辑频道
async function editChannel(id) {
  try {
    const response = await fetch(`${API_BASE_URL}/channels/${id}`, {
      headers: getAuthHeaders()
    });
    const result = await response.json();
    if (!response.ok) {
      showAlert(result.error || '获取频道失败', 'danger');
      return;
    }
    const channel = result.data;
    editingChannelId = channel.id;
    document.getElementById('channelName').value = channel.channel_name || '';
    document.getElementById('channelCategory').value = channel.category || '';
    document.getElementById('channelStatus').value = String(channel.status ?? 0);
    const modal = new bootstrap.Modal(document.getElementById('editChannelModal'));
    modal.show();
  } catch (error) {
    console.error('获取频道信息失败:', error);
    showAlert('获取频道信息失败', 'danger');
  }
}

// 保存频道
async function saveChannel(event) {
  if (event) event.preventDefault();
  const channelId = editingChannelId;
  if (!channelId) {
    showAlert('频道ID无效', 'danger');
    return;
  }
  const channel_name = document.getElementById('channelName').value.trim();
  const category = document.getElementById('channelCategory').value.trim();
  const status = Number(document.getElementById('channelStatus').value);
  const payload = { channel_name, category, status };
  try {
    const response = await fetch(`${API_BASE_URL}/channels/${channelId}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload)
    });
    const result = await response.json();
    if (response.ok) {
      showAlert('频道更新成功', 'success');
      editingChannelId = null;
      bootstrap.Modal.getInstance(document.getElementById('editChannelModal')).hide();
      loadChannels();
    } else {
      showAlert(result.error || '更新失败', 'danger');
    }
} catch (error) {
    console.error('更新频道失败:', error);
    showAlert('更新频道失败', 'danger');
  } 
}

// ==================== 频道模板库功能 ====================

let templateData = null;
let selectedCategories = [];

// 加载频道模板统计
async function loadChannelTemplates() {
  try {
    const response = await fetch(`${API_BASE_URL}/channel-template/templates`, {
      headers: getAuthHeaders()
    });
    
    if (!response.ok) {
      if (response.status === 401) {
        // Token失效，跳转到登录页
        logout();
        return;
      }
      console.error('加载频道模板失败:', response.status);
      return;
    }
    
    const result = await response.json();
    
    if (result.data) {
      templateData = result.data;
      
      // 更新统计（添加null检查）
      const totalEl = document.getElementById('template-total');
      if (totalEl) {
        totalEl.textContent = result.data.total;
      }
      
      // 渲染分类徽章（添加null检查）
      const categoriesContainer = document.getElementById('category-badges');
      if (categoriesContainer) {
        categoriesContainer.innerHTML = '';
        
        Object.entries(result.data.categories).forEach(([category, count]) => {
          const badge = document.createElement('span');
          badge.className = 'badge bg-info';
          badge.textContent = `${category} (${count})`;
          categoriesContainer.appendChild(badge);
        });
      }
    }
  } catch (error) {
    console.error('加载频道模板失败:', error);
  }
}

// 显示导入模态框
async function showImportModal() {
  const modal = new bootstrap.Modal(document.getElementById('importChannelModal'));
  
  // 加载账户列表
  try {
    const response = await fetch(`${API_BASE_URL}/accounts`, {
      headers: getAuthHeaders()
    });
    const data = await response.json();
    
    const accountSelect = document.getElementById('import-account-id');
    accountSelect.innerHTML = '<option value="">请选择账户...</option>';
    data.data.forEach(account => {
      const option = document.createElement('option');
      option.value = account.id;
      option.textContent = account.username;
      accountSelect.appendChild(option);
    });
  } catch (error) {
    console.error('加载账户列表失败:', error);
  }
  
  // 加载分类选择
  if (templateData) {
    const categoriesContainer = document.getElementById('import-categories');
    categoriesContainer.innerHTML = '';
    selectedCategories = [];
    
    Object.keys(templateData.categories).forEach(category => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'btn btn-outline-primary btn-sm';
      btn.textContent = category;
      btn.onclick = () => toggleCategory(category, btn);
      categoriesContainer.appendChild(btn);
    });
  }
  
  document.getElementById('import-preview').style.display = 'none';
  modal.show();
}

// 切换分类选择
function toggleCategory(category, btn) {
  const index = selectedCategories.indexOf(category);
  if (index > -1) {
    selectedCategories.splice(index, 1);
    btn.classList.remove('btn-primary');
    btn.classList.add('btn-outline-primary');
  } else {
    selectedCategories.push(category);
    btn.classList.remove('btn-outline-primary');
    btn.classList.add('btn-primary');
  }
  
  // 更新预览
  if (selectedCategories.length > 0 && templateData) {
    const count = selectedCategories.reduce((sum, cat) => sum + (templateData.categories[cat] || 0), 0);
    document.getElementById('import-count').textContent = count;
    document.getElementById('import-preview').style.display = 'block';
  } else {
    document.getElementById('import-preview').style.display = 'none';
  }
}

// 执行导入
async function executeImport() {
  const accountId = document.getElementById('import-account-id').value;
  const sourceName = document.getElementById('import-source-name').value.trim();
  const overwrite = document.getElementById('import-overwrite').checked;
  
  if (!accountId) {
    showAlert('请选择账户', 'warning');
    return;
  }
  
  if (!sourceName) {
    showAlert('请输入源名称', 'warning');
    return;
  }
  
  if (selectedCategories.length === 0) {
    showAlert('请至少选择一个分类', 'warning');
    return;
  }
  
  const payload = {
    account_id: parseInt(accountId),
    source_name: sourceName,
    categories: selectedCategories,
    overwrite: overwrite
  };
  
  try {
    // 显示加载状态
    const btn = event.target;
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>导入中...';
    
    const response = await fetch(`${API_BASE_URL}/channel-template/import`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload)
    });
    
    const result = await response.json();
    
    btn.disabled = false;
    btn.innerHTML = originalText;
    
    if (response.ok) {
      showAlert(`成功导入 ${result.data.imported} 个频道`, 'success');
      bootstrap.Modal.getInstance(document.getElementById('importChannelModal')).hide();
      loadChannels();
    } else {
      showAlert(result.error || '导入失败', 'danger');
    }
  } catch (error) {
    console.error('导入频道失败:', error);
    showAlert('导入频道失败', 'danger');
  }
}

// 批量选择功能
let selectedChannelIds = [];

function toggleSelectAllChannels() {
  const checkbox = document.getElementById('select-all-channels');
  const checkboxes = document.querySelectorAll('.channel-checkbox');
  
  checkboxes.forEach(cb => {
    cb.checked = checkbox.checked;
  });
  
  updateSelectedChannels();
}

function updateSelectedChannels() {
  selectedChannelIds = [];
  document.querySelectorAll('.channel-checkbox:checked').forEach(cb => {
    selectedChannelIds.push(parseInt(cb.dataset.id));
  });
  
  const batchDeleteBtn = document.getElementById('batch-delete-btn');
  if (selectedChannelIds.length > 0) {
    batchDeleteBtn.style.display = 'inline-block';
  } else {
    batchDeleteBtn.style.display = 'none';
  }
}

// 批量删除频道
async function batchDeleteChannels() {
  if (selectedChannelIds.length === 0) {
    showAlert('请先选择要删除的频道', 'warning');
    return;
  }
  
  if (!confirm(`确定要删除选中的 ${selectedChannelIds.length} 个频道吗？`)) {
    return;
  }
  
  try {
    const response = await fetch(`${API_BASE_URL}/channel-template/batch-delete`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ channel_ids: selectedChannelIds })
    });
    
    const result = await response.json();
    
    if (response.ok) {
      showAlert(`成功删除 ${result.deleted} 个频道`, 'success');
      selectedChannelIds = [];
      document.getElementById('select-all-channels').checked = false;
      loadChannels();
    } else {
      showAlert(result.error || '批量删除失败', 'danger');
    }
  } catch (error) {
    console.error('批量删除失败:', error);
    showAlert('批量删除失败', 'danger');
  }
}

// 同步频道分类（根据channel_id匹配模板库）
async function syncChannelCategories() {
  // 获取当前选择的账户对应的源ID
  const accountId = document.getElementById('account-filter')?.value;
  
  if (!accountId) {
    showAlert('请先选择一个账户', 'warning');
    return;
  }
  
  if (!confirm('将根据频道ID自动匹配模板库，更新频道名称和分类信息。是否继续？')) {
    return;
  }
  
  try {
    // 先获取账户信息得到source_id
    const accountResponse = await fetch(`${API_BASE_URL}/accounts/${accountId}`, {
      headers: getAuthHeaders()
    });
    const accountData = await accountResponse.json();
    
    if (!accountData.data || !accountData.data.source_id) {
      showAlert('该账户没有关联的直播源', 'warning');
      return;
    }
    
    const sourceId = accountData.data.source_id;
    
    // 显示加载提示
    showAlert('正在同步分类信息...', 'info');
    
    // 调用同步API
    const response = await fetch(`${API_BASE_URL}/channel-template/sync-categories/${sourceId}`, {
      method: 'POST',
      headers: getAuthHeaders()
    });
    
    const result = await response.json();
    
    if (response.ok) {
      showAlert(`同步完成！更新了 ${result.data.updated} 个频道`, 'success');
      loadChannels();
    } else {
      showAlert(result.error || '同步失败', 'danger');
    }
  } catch (error) {
    console.error('同步频道分类失败:', error);
    showAlert('同步频道分类失败', 'danger');
  }
}

// 显示提示信息
function showAlert(message, type) {
  const alertDiv = document.createElement('div');
  alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
  alertDiv.style.zIndex = '9999';
  alertDiv.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;
  document.body.appendChild(alertDiv);
  
  setTimeout(() => {
    alertDiv.remove();
  }, 3000);
}

// ============ 管理员管理函数 ============
let currentUser = null;
let isDefaultAdmin = false;
let editingAccountId = null; // 存储正在编辑的账户ID
let editingChannelId = null; // 存储正在编辑的频道ID
let editingTemplateId = null; // 存储正在编辑的模板ID

// ==================== 频道模板管理 ====================

async function loadTemplates() {
  try {
    const groupFilter = document.getElementById('templateGroupFilter').value;
    const url = groupFilter 
      ? `${API_BASE_URL}/channel-template/templates?group_title=${encodeURIComponent(groupFilter)}`
      : `${API_BASE_URL}/channel-template/templates`;
    
    const response = await fetch(url, {
      headers: getAuthHeaders()
    });
    const result = await response.json();
    
    if (!result.success) {
      showAlert('加载模板失败: ' + result.error, 'danger');
      return;
    }
    
    const tbody = document.getElementById('templateTableBody');
    tbody.innerHTML = '';
    
    result.data.forEach(template => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td>${template.id}</td>
        <td>${template.channel_id}</td>
        <td>${template.name}</td>
        <td><span class="badge bg-info">${template.group_title}</span></td>
        <td>${new Date(template.created_at).toLocaleString()}</td>
        <td>
          <button class="btn btn-sm btn-primary" onclick="showEditTemplateModal(${template.id})">
            <i class="bi bi-pencil"></i> 编辑
          </button>
          <button class="btn btn-sm btn-danger" onclick="deleteTemplate(${template.id})">
            <i class="bi bi-trash"></i> 删除
          </button>
        </td>
      `;
      tbody.appendChild(row);
    });
    
  } catch (error) {
    console.error('加载模板失败:', error);
    showAlert('加载模板失败', 'danger');
  }
}

async function loadTemplateStatistics() {
  try {
    const response = await fetch(`${API_BASE_URL}/channel-template/statistics`, {
      headers: getAuthHeaders()
    });
    const result = await response.json();
    
    if (!result.success) {
      return;
    }
    
    // 更新总数
    document.getElementById('templateTotalCount').textContent = result.data.total;
    
    // 更新分类统计
    const statsContainer = document.getElementById('templateCategoryStats');
    statsContainer.innerHTML = '';
    
    for (const [category, count] of Object.entries(result.data.groups)) {
      const badge = document.createElement('span');
      badge.className = 'badge bg-secondary';
      badge.textContent = `${category}: ${count}`;
      statsContainer.appendChild(badge);
    }
    
  } catch (error) {
    console.error('加载统计失败:', error);
  }
}

async function loadTemplateGroups() {
  try {
    const response = await fetch(`${API_BASE_URL}/channel-template/groups`, {
      headers: getAuthHeaders()
    });
    const result = await response.json();
    
    if (!result.success) {
      return;
    }
    
    // 更新筛选下拉框
    const filterSelect = document.getElementById('templateGroupFilter');
    const modalSelect = document.getElementById('templateGroupTitle');
    
    // 清空现有选项（保留第一个"全部分组"）
    filterSelect.innerHTML = '<option value="">全部分组</option>';
    modalSelect.innerHTML = '<option value="">请选择分组</option>';
    
    result.data.forEach(group => {
      filterSelect.innerHTML += `<option value="${group}">${group}</option>`;
      modalSelect.innerHTML += `<option value="${group}">${group}</option>`;
    });
    
  } catch (error) {
    console.error('加载分组失败:', error);
  }
}

function showAddTemplateModal() {
  editingTemplateId = null;
  document.getElementById('templateModalTitle').textContent = '添加频道模板';
  document.getElementById('templateId').value = '';
  document.getElementById('templateChannelId').value = '';
  document.getElementById('templateChannelId').disabled = false;
  document.getElementById('templateName').value = '';
  document.getElementById('templateGroupTitle').value = '';
  
  const modal = new bootstrap.Modal(document.getElementById('templateModal'));
  modal.show();
}

async function showEditTemplateModal(templateId) {
  try {
    const response = await fetch(`${API_BASE_URL}/channel-template/templates/${templateId}`, {
      headers: getAuthHeaders()
    });
    const result = await response.json();
    
    if (!result.success) {
      showAlert('获取模板失败', 'danger');
      return;
    }
    
    editingTemplateId = templateId;
    document.getElementById('templateModalTitle').textContent = '编辑频道模板';
    document.getElementById('templateId').value = result.data.id;
    document.getElementById('templateChannelId').value = result.data.channel_id;
    document.getElementById('templateChannelId').disabled = true; // channel_id不可修改
    document.getElementById('templateName').value = result.data.name;
    document.getElementById('templateGroupTitle').value = result.data.group_title;
    
    const modal = new bootstrap.Modal(document.getElementById('templateModal'));
    modal.show();
    
  } catch (error) {
    console.error('获取模板失败:', error);
    showAlert('获取模板失败', 'danger');
  }
}

async function saveTemplate() {
  const channelId = document.getElementById('templateChannelId').value.trim();
  const name = document.getElementById('templateName').value.trim();
  const groupTitle = document.getElementById('templateGroupTitle').value;
  
  if (!channelId || !name || !groupTitle) {
    showAlert('请填写所有必填字段', 'warning');
    return;
  }
  
  try {
    let url, method;
    const payload = { name, group_title: groupTitle };
    
    if (editingTemplateId) {
      // 编辑模式
      url = `${API_BASE_URL}/channel-template/templates/${editingTemplateId}`;
      method = 'PUT';
    } else {
      // 添加模式
      url = `${API_BASE_URL}/channel-template/templates`;
      method = 'POST';
      payload.channel_id = channelId;
    }
    
    const response = await fetch(url, {
      method: method,
      headers: getAuthHeaders(),
      body: JSON.stringify(payload)
    });
    
    const result = await response.json();
    
    if (result.success) {
      showAlert(result.message, 'success');
      bootstrap.Modal.getInstance(document.getElementById('templateModal')).hide();
      loadTemplates();
      loadTemplateStatistics();
    } else {
      showAlert(result.message, 'danger');
    }
    
  } catch (error) {
    console.error('保存模板失败:', error);
    showAlert('保存模板失败', 'danger');
  }
}

async function deleteTemplate(templateId) {
  if (!confirm('确定要删除此频道模板吗？')) {
    return;
  }
  
  try {
    const response = await fetch(`${API_BASE_URL}/channel-template/templates/${templateId}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });
    
    const result = await response.json();
    
    if (result.success) {
      showAlert(result.message, 'success');
      loadTemplates();
      loadTemplateStatistics();
    } else {
      showAlert(result.message, 'danger');
    }
    
  } catch (error) {
    console.error('删除模板失败:', error);
    showAlert('删除模板失败', 'danger');
  }
}

// ==================== 管理员管理 ====================

async function loadAdmins() {
  try {
    const response = await fetch(`${API_BASE_URL}/admins`, {
      headers: getAuthHeaders()
    });
    const data = await response.json();
    
    const tbody = document.getElementById('adminTableBody');
    tbody.innerHTML = '';
    
    if (data.data.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">暂无数据</td></tr>';
      return;
    }
    
    data.data.forEach(admin => {
      const isDefault = admin.is_default === 1;
      const isActive = admin.is_active === 1;
      
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>
          <strong>${admin.username}</strong>
          ${isDefault ? '<span class="badge bg-primary ms-2">默认</span>' : ''}
        </td>
        <td><span class="badge bg-info">管理员</span></td>
        <td><span class="badge ${isActive ? 'bg-success' : 'bg-danger'}">${isActive ? '启用' : '停用'}</span></td>
        <td>${new Date(admin.created_at).toLocaleDateString()}</td>
        <td>
          ${renderAdminActions(admin)}
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (error) {
    console.error('加载管理员列表失败:', error);
    showAlert('加载失败: ' + error.message, 'danger');
  }
}

function renderAdminActions(admin) {
  const isDefault = admin.is_default === 1;
  // 只有默认管理员才能对其他管理员进行操作
  if (isDefaultAdmin && !isDefault) {
    const isActive = admin.is_active === 1;
    return `
      <button class="btn btn-sm btn-warning" onclick="editAdmin(${admin.id})">修改密码</button>
      <button class="btn btn-sm btn-${isActive ? 'danger' : 'success'}" onclick="toggleAdminStatus(${admin.id}, ${isActive})">
        ${isActive ? '禁用' : '启用'}
      </button>
      <button class="btn btn-sm btn-danger" onclick="deleteAdmin(${admin.id})">删除</button>
    `;
  }
  return '-';
}

function showAddAdminModal() {
  const modal = new bootstrap.Modal(document.getElementById('addAdminModal'));
  document.getElementById('addAdminForm').reset();
  modal.show();
}

async function createAdminFromModal() {
  const username = document.getElementById('newAdminUsername').value.trim();
  const password = document.getElementById('newAdminPassword').value;
  const passwordConfirm = document.getElementById('newAdminPasswordConfirm').value;
  
  if (!username || !password || !passwordConfirm) {
    showAlert('请填写所有必填项', 'warning');
    return;
  }
  
  if (password !== passwordConfirm) {
    showAlert('两次输入的密码不一致', 'warning');
    return;
  }
  
  try {
    const response = await fetch(`${API_BASE_URL}/admins`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ username, password })
    });
    
    if (response.ok) {
      showAlert('管理员创建成功', 'success');
      bootstrap.Modal.getInstance(document.getElementById('addAdminModal')).hide();
      loadAdmins();
    } else {
      const error = await response.json();
      showAlert(error.error || '创建失败', 'danger');
    }
  } catch (error) {
    console.error('创建管理员失败:', error);
    showAlert('创建失败', 'danger');
  }
}

async function editAdmin(adminId) {
  try {
    // 获取管理员信息
    const response = await fetch(`${API_BASE_URL}/admins`, {
      headers: getAuthHeaders()
    });
    const data = await response.json();
    
    // 查找当前管理员
    const admin = data.data.find(a => a.id === adminId);
    if (!admin) {
      showAlert('管理员不存在', 'danger');
      return;
    }
    
    // 填充表单
    document.getElementById('editAdminId').value = adminId;
    document.getElementById('editAdminUsername').value = admin.username;
    document.getElementById('editAdminPassword').value = '';
    document.getElementById('editAdminPasswordConfirm').value = '';
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('editAdminModal'));
    modal.show();
  } catch (error) {
    console.error('获取管理员信息失败:', error);
    showAlert('获取管理员信息失败', 'danger');
  }
}

async function saveAdminPassword() {
  const adminId = document.getElementById('editAdminId').value;
  const newPassword = document.getElementById('editAdminPassword').value;
  const passwordConfirm = document.getElementById('editAdminPasswordConfirm').value;
  
  if (!newPassword || !passwordConfirm) {
    showAlert('请填写所有必填项', 'warning');
    return;
  }
  
  if (newPassword !== passwordConfirm) {
    showAlert('两次输入的密码不一致', 'warning');
    return;
  }
  
  try {
    const response = await fetch(`${API_BASE_URL}/admins/${adminId}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify({ new_password: newPassword })
    });
    
    if (response.ok) {
      showAlert('管理员密码修改成功', 'success');
      bootstrap.Modal.getInstance(document.getElementById('editAdminModal')).hide();
      loadAdmins();
    } else {
      const error = await response.json();
      showAlert(error.error || '修改失败', 'danger');
    }
  } catch (error) {
    console.error('修改管理员密码失败:', error);
    showAlert('修改失败', 'danger');
  }
}

async function toggleAdminStatus(adminId, currentStatus) {
  try {
    const response = await fetch(`${API_BASE_URL}/admins/${adminId}/toggle`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify({ is_active: !currentStatus })
    });
    
    if (response.ok) {
      showAlert(currentStatus ? '管理员已禁用' : '管理员已启用', 'success');
      loadAdmins();
    } else {
      const error = await response.json();
      showAlert(error.error || '操作失败', 'danger');
    }
  } catch (error) {
    console.error('切换管理员状态失败:', error);
    showAlert('操作失败', 'danger');
  }
}

async function deleteAdmin(adminId) {
  if (!confirm('确定要删除此管理员吗？')) return;
  
  try {
    const response = await fetch(`${API_BASE_URL}/admins/${adminId}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });
    
    if (response.ok) {
      showAlert('管理员删除成功', 'success');
      loadAdmins();
    } else {
      const error = await response.json();
      showAlert(error.error || '删除失败', 'danger');
    }
  } catch (error) {
    console.error('删除管理员失败:', error);
    showAlert('删除失败', 'danger');
  }
}

// ============ 定时任务函数 ============

// 定时任务编辑状态
let scheduleEditState = {
  isEditing: false,
  taskId: null,
  originalData: {}
};

// 将任务类型代码转换为显示名称
function getTaskTypeName(taskType) {
  const typeMap = {
    'fetch_channels': '获取直播源',
    'fetch_epg': '获取电子节目表',
    'sync_data': '同步数据'
  };
  return typeMap[taskType] || taskType;
}

// 将重复类型代码转换为显示名称
function getRepeatTypeName(repeatType) {
  const repeatMap = {
    'once': '仅一次',
    'daily': '每天',
    'weekly': '每周',
    'monthly': '每月'
  };
  return repeatMap[repeatType] || repeatType;
}

async function loadScheduleTasks() {
  try {
    // 先加载账户列表到下拉框和映射
    const accountsResp = await fetch(`${API_BASE_URL}/accounts`, {
      headers: getAuthHeaders()
    });
    const accountsData = await accountsResp.json();
    
    // 创建账户ID到用户名的映射
    const accountMap = {};
    const accountSelect = document.getElementById('accountId');
    accountSelect.innerHTML = '<option value="">请选择账户...</option>';
    accountsData.data.forEach(account => {
      accountMap[account.id] = account.username;
      const option = document.createElement('option');
      option.value = account.id;
      option.textContent = account.username;
      accountSelect.appendChild(option);
    });
    
    // 加载任务列表
    const response = await fetch(`${API_BASE_URL}/schedule/tasks`, {
      headers: getAuthHeaders()
    });
    const data = await response.json();
    
    const tbody = document.getElementById('scheduleTableBody');
    tbody.innerHTML = '';
    
    const tasks = data.tasks || [];
    if (tasks.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">暂无数据</td></tr>';
      return;
    }
    
    tasks.forEach(task => {
      const tr = document.createElement('tr');
      const accountName = accountMap[task.account_id] || `账户 ${task.account_id}`;
      const taskTypeName = getTaskTypeName(task.task_type);
      const repeatTypeName = getRepeatTypeName(task.repeat_type);
      
      tr.innerHTML = `
        <td>${task.id}</td>
        <td>${accountName}</td>
        <td>${taskTypeName}</td>
        <td>${task.schedule_time || '-'}</td>
        <td>${repeatTypeName}</td>
        <td><span class="badge ${task.is_enabled ? 'bg-success' : 'bg-secondary'}">${task.is_enabled ? '启用' : '禁用'}</span></td>
        <td>
          <button class="btn btn-sm btn-info" onclick="executeScheduleTaskNow(${task.id})" title="立即执行一次">
            <i class="bi bi-play-circle"></i>
          </button>
          <button class="btn btn-sm btn-primary" onclick="editScheduleTask(${task.id})">编辑</button>
          <button class="btn btn-sm btn-warning" onclick="toggleScheduleTask(${task.id}, ${task.is_enabled})">
            ${task.is_enabled ? '禁用' : '启用'}
          </button>
          <button class="btn btn-sm btn-danger" onclick="deleteScheduleTask(${task.id})">删除</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (error) {
    console.error('加载定时任务失败:', error);
    showAlert('加载失败: ' + error.message, 'danger');
  }
}

async function submitScheduleForm(event) {
  event.preventDefault();
  
  const accountId = document.getElementById('accountId').value;
  const taskType = document.getElementById('taskType').value;
  const scheduleTime = document.getElementById('scheduleTime').value;
  const repeatType = document.getElementById('repeatType').value;
  const channelFilters = document.getElementById('channelFilters').value;
  const filterSd = document.getElementById('filterSd').checked;
  const editTaskId = document.getElementById('editTaskId').value;
  
  if (!accountId) {
    showAlert('请选择账户', 'warning');
    return;
  }
  
  try {
    let response;
    
    if (scheduleEditState.isEditing && editTaskId) {
      // 编辑现有任务
      response = await fetch(`${API_BASE_URL}/schedule/tasks/${editTaskId}`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          account_id: parseInt(accountId),
          task_type: taskType,
          schedule_time: scheduleTime,
          repeat_type: repeatType,
          channel_filters: channelFilters,
          filter_sd: filterSd
        })
      });
      
      if (response.ok) {
        showAlert('任务更新成功', 'success');
        // 清除编辑状态并隐藏按钮
        scheduleEditState.isEditing = false;
        scheduleEditState.taskId = null;
        scheduleEditState.originalData = {};
        document.getElementById('editTaskId').value = '';
        document.getElementById('scheduleFormTitle').textContent = '创建定时任务';
        document.getElementById('scheduleSubmitBtn').textContent = '创建任务';
        document.getElementById('scheduleResetBtn').style.display = 'none';
        document.getElementById('scheduleCancelBtn').style.display = 'none';
        document.getElementById('scheduleForm').reset();
        loadScheduleTasks();
      } else {
        const error = await response.json();
        showAlert(error.error || '更新失败', 'danger');
      }
    } else {
      // 创建新任务
      response = await fetch(`${API_BASE_URL}/schedule/tasks`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          account_id: parseInt(accountId),
          task_type: taskType,
          schedule_time: scheduleTime,
          repeat_type: repeatType,
          channel_filters: channelFilters,
          filter_sd: filterSd
        })
      });
      
      if (response.ok) {
        showAlert('任务创建成功', 'success');
        document.getElementById('scheduleForm').reset();
        loadScheduleTasks();
      } else {
        const error = await response.json();
        showAlert(error.error || '创建失败', 'danger');
      }
    }
  } catch (error) {
    console.error('提交任务失败:', error);
    showAlert('提交失败', 'danger');
  }
}

function resetScheduleForm() {
  if (scheduleEditState.isEditing) {
    // 恢复编辑前的数据
    const orig = scheduleEditState.originalData;
    document.getElementById('accountId').value = orig.accountId;
    document.getElementById('taskType').value = orig.taskType;
    document.getElementById('scheduleTime').value = orig.scheduleTime;
    document.getElementById('repeatType').value = orig.repeatType;
    document.getElementById('channelFilters').value = orig.channelFilters || '';
    document.getElementById('filterSd').checked = orig.filterSd === 1 || orig.filterSd === true;
  } else {
    // 清空表单
    document.getElementById('scheduleForm').reset();
  }
}

function cancelScheduleEdit() {
  // 取消编辑，恢复为创建模式
  scheduleEditState.isEditing = false;
  scheduleEditState.taskId = null;
  scheduleEditState.originalData = {};
  
  document.getElementById('editTaskId').value = '';
  document.getElementById('scheduleFormTitle').textContent = '创建定时任务';
  document.getElementById('scheduleSubmitBtn').textContent = '创建任务';
  document.getElementById('scheduleResetBtn').style.display = 'none';
  document.getElementById('scheduleCancelBtn').style.display = 'none';
  
  document.getElementById('scheduleForm').reset();
}

async function toggleScheduleTask(taskId, currentStatus) {
  try {
    const response = await fetch(`${API_BASE_URL}/schedule/tasks/${taskId}/${currentStatus ? 'disable' : 'enable'}`, {
      method: 'PUT',
      headers: getAuthHeaders()
    });
    
    if (response.ok) {
      showAlert(currentStatus ? '任务已禁用' : '任务已启用', 'success');
      loadScheduleTasks();
    } else {
      const error = await response.json();
      showAlert(error.error || '操作失败', 'danger');
    }
  } catch (error) {
    console.error('切换任务状态失败:', error);
    showAlert('操作失败', 'danger');
  }
}

async function editScheduleTask(taskId) {
  try {
    // 获取任务详情
    const response = await fetch(`${API_BASE_URL}/schedule/tasks/${taskId}`, {
      headers: getAuthHeaders()
    });
    const data = await response.json();
    const task = data.task;
    
    if (!task) {
      showAlert('任务不存在', 'danger');
      return;
    }
    
    // 保存原始数据用于重置
    scheduleEditState.isEditing = true;
    scheduleEditState.taskId = taskId;
    scheduleEditState.originalData = {
      accountId: task.account_id,
      taskType: task.task_type,
      scheduleTime: task.schedule_time,
      repeatType: task.repeat_type,
      channelFilters: task.channel_filters,
      filterSd: task.filter_sd
    };
    
    // 回填数据到表单
    document.getElementById('accountId').value = task.account_id;
    document.getElementById('taskType').value = task.task_type;
    document.getElementById('scheduleTime').value = task.schedule_time;
    document.getElementById('repeatType').value = task.repeat_type;
    document.getElementById('channelFilters').value = task.channel_filters || '';
    document.getElementById('filterSd').checked = task.filter_sd === 1;
    document.getElementById('editTaskId').value = taskId;
    
    // 修改UI文本
    document.getElementById('scheduleFormTitle').textContent = '修改定时任务';
    document.getElementById('scheduleSubmitBtn').textContent = '保存任务';
    document.getElementById('scheduleResetBtn').style.display = 'inline-block';
    document.getElementById('scheduleCancelBtn').style.display = 'inline-block';
    
    // 滚动到表单
    document.getElementById('scheduleForm').scrollIntoView({ behavior: 'smooth' });
    
  } catch (error) {
    console.error('加载任务失败:', error);
    showAlert('加载失败', 'danger');
  }
}

async function deleteScheduleTask(taskId) {
  if (!confirm('确定要删除此任务吗？')) return;
  
  try {
    const response = await fetch(`${API_BASE_URL}/schedule/tasks/${taskId}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });
    
    if (response.ok) {
      showAlert('任务删除成功', 'success');
      loadScheduleTasks();
    } else {
      const error = await response.json();
      showAlert(error.error || '删除失败', 'danger');
    }
  } catch (error) {
    console.error('删除任务失败:', error);
    showAlert('删除失败', 'danger');
  }
}

// 立即执行定时任务
async function executeScheduleTaskNow(taskId) {
  // 创建执行中提示
  const btn = event.target.closest('button');
  const originalContent = btn.innerHTML;
  btn.innerHTML = '<i class="bi bi-hourglass-split"></i> 执行中...';
  btn.disabled = true;
  
  try {
    const response = await fetch(`${API_BASE_URL}/schedule/tasks/${taskId}/execute`, {
      method: 'POST',
      headers: getAuthHeaders()
    });
    
    const data = await response.json();
    
    if (response.ok) {
      showAlert('任务执行成功', 'success');
      // 短暂延迟后刷新任务列表
      setTimeout(() => loadScheduleTasks(), 1000);
    } else {
      showAlert(data.error || data.message || '任务执行失败', 'danger');
    }
  } catch (error) {
    console.error('执行任务失败:', error);
    showAlert('执行失败: ' + error.message, 'danger');
  } finally {
    // 恢复按钮状态
    btn.innerHTML = originalContent;
    btn.disabled = false;
  }
}

// ============ 日志管理函数 ============
// 切换系统日志类型
function switchSystemLog(type) {
  if (type === 'system') {
    document.getElementById('systemLogContent').style.display = 'block';
    document.getElementById('operationLogContent').style.display = 'none';
    loadSystemLogs();
  } else {
    document.getElementById('systemLogContent').style.display = 'none';
    document.getElementById('operationLogContent').style.display = 'block';
    loadOperationLogs();
  }
}

function logLevelClass(level) {
  if (level === 'error') return 'danger';
  if (level === 'warning') return 'warning';
  if (level === 'success') return 'success';
  return 'info';
}

async function fetchLogs(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') {
      query.append(k, v);
    }
  });
  const response = await fetch(`${API_BASE_URL}/logs?${query.toString()}`, {
    headers: getAuthHeaders()
  });
  const data = await response.json();
  if (!response.ok || data.success === false) {
    throw new Error(data.error || '获取日志失败');
  }
  return data;
}

// 仪表盘：系统日志
async function loadSystemLogs() {
  const logList = document.getElementById('systemLogList');
  const isEmpty = logList.innerHTML.includes('加载中') || logList.innerHTML === '';
  if (isEmpty) {
    logList.innerHTML = '<div class="text-center text-muted py-3">加载中...</div>';
  }
  try {
    const data = await fetchLogs({ type: 'system', page_size: DASHBOARD_LOG_PAGE_SIZE, page: 1 });
    renderSimpleLogs(logList, data.items);
  } catch (error) {
    if (isEmpty) {
      logList.innerHTML = `<div class="text-center text-danger py-3">${error.message}</div>`;
    }
  }
}

// 仪表盘：操作日志
async function loadOperationLogs() {
  const logList = document.getElementById('operationLogList');
  const isEmpty = logList.innerHTML.includes('加载中') || logList.innerHTML === '';
  if (isEmpty) {
    logList.innerHTML = '<div class="text-center text-muted py-3">加载中...</div>';
  }
  try {
    const data = await fetchLogs({ type: 'operation', page_size: DASHBOARD_LOG_PAGE_SIZE, page: 1 });
    renderOperationLogs(logList, data.items);
  } catch (error) {
    if (isEmpty) {
      logList.innerHTML = `<div class="text-center text-danger py-3">${error.message}</div>`;
    }
  }
}

// 仪表盘：任务日志
async function loadTaskLogs() {
  const logList = document.getElementById('taskLogList');
  const isEmpty = logList.innerHTML.includes('加载中') || logList.innerHTML === '';
  if (isEmpty) {
    logList.innerHTML = '<div class="text-center text-muted py-3">加载中...</div>';
  }
  try {
    const data = await fetchLogs({ type: 'task', page_size: DASHBOARD_LOG_PAGE_SIZE, page: 1 });
    renderTaskLogs(logList, data.items);
  } catch (error) {
    if (isEmpty) {
      logList.innerHTML = `<div class="text-center text-danger py-3">${error.message}</div>`;
    }
  }
}

// 启动仪表盘日志轮询
function startDashboardLogPolling() {
  // 清除已存在的轮询
  stopDashboardLogPolling();
  
  // 系统日志轮询
  dashboardLogPollingIntervals.system = setInterval(() => {
    loadSystemLogs();
  }, DASHBOARD_LOG_POLL_INTERVAL);
  
  // 操作日志轮询
  dashboardLogPollingIntervals.operation = setInterval(() => {
    loadOperationLogs();
  }, DASHBOARD_LOG_POLL_INTERVAL);
  
  // 任务日志轮询
  dashboardLogPollingIntervals.task = setInterval(() => {
    loadTaskLogs();
  }, DASHBOARD_LOG_POLL_INTERVAL);
}

// 停止仪表盘日志轮询
function stopDashboardLogPolling() {
  Object.keys(dashboardLogPollingIntervals).forEach(key => {
    if (dashboardLogPollingIntervals[key]) {
      clearInterval(dashboardLogPollingIntervals[key]);
      dashboardLogPollingIntervals[key] = null;
    }
  });
}

function renderSimpleLogs(container, logs) {
  container.innerHTML = '';
  if (!logs || logs.length === 0) {
    container.innerHTML = '<div class="text-center text-muted py-3">暂无日志</div>';
    return;
  }
  logs.forEach(log => {
    const levelClass = logLevelClass(log.level);
    const levelIcon = log.level === 'error' ? 'x-circle' :
                     log.level === 'warning' ? 'exclamation-triangle' :
                     log.level === 'success' ? 'check-circle' : 'info-circle';
    const logItem = document.createElement('div');
    logItem.className = 'list-group-item';
    logItem.innerHTML = `
      <div class="d-flex w-100 justify-content-between align-items-start">
        <div class="flex-grow-1">
          <span class="badge bg-${levelClass} me-2">
            <i class="bi bi-${levelIcon}"></i> ${(log.level || 'INFO').toUpperCase()}
          </span>
          <span>${log.message || ''}</span>
        </div>
        <small class="text-muted">${log.created_at || ''}</small>
      </div>
    `;
    container.appendChild(logItem);
  });
}

function renderOperationLogs(container, logs) {
  container.innerHTML = '';
  if (!logs || logs.length === 0) {
    container.innerHTML = '<div class="text-center text-muted py-3">暂无日志</div>';
    return;
  }
  logs.forEach(log => {
    const logItem = document.createElement('div');
    logItem.className = 'list-group-item';
    logItem.innerHTML = `
      <div class="d-flex w-100 justify-content-between align-items-start">
        <div class="flex-grow-1">
          <span class="badge bg-primary me-2">${log.username || '系统'}</span>
          <strong>${log.action || '操作'}</strong>
          <p class="mb-0 mt-1 text-muted" style="font-size: 0.9rem;">${log.message || ''}</p>
        </div>
        <small class="text-muted">${log.created_at || ''}</small>
      </div>
    `;
    container.appendChild(logItem);
  });
}

function renderTaskLogs(container, logs) {
  container.innerHTML = '';
  if (!logs || logs.length === 0) {
    container.innerHTML = '<div class="text-center text-muted py-3">暂无日志</div>';
    return;
  }
  
  // 过滤日志：隐藏进行中的日志，如果有对应的成功/失败日志
  const filteredLogs = filterRunningLogs(logs);
  
  if (filteredLogs.length === 0) {
    container.innerHTML = '<div class="text-center text-muted py-3">暂无日志</div>';
    return;
  }
  
  filteredLogs.forEach(log => {
    const status = log.status || 'info';
    const statusClass = status === 'success' ? 'success' :
                        status === 'failed' ? 'danger' :
                        status === 'running' ? 'info' : 'secondary';
    const statusIcon = status === 'success' ? 'check-circle-fill' :
                       status === 'failed' ? 'x-circle-fill' :
                       status === 'running' ? 'arrow-repeat' : 'clock';
    const statusText = status === 'success' ? '成功' :
                       status === 'failed' ? '失败' :
                       status === 'running' ? '执行中' : '等待';
    const spinClass = status === 'running' ? ' task-icon-spin' : '';
    const logItem = document.createElement('div');
    logItem.className = 'list-group-item';
    logItem.innerHTML = `
      <div class="d-flex w-100 justify-content-between align-items-start">
        <div class="flex-grow-1">
          <div class="d-flex align-items-center mb-1">
            <i class="bi bi-${statusIcon} text-${statusClass} me-2${spinClass}"></i>
            <strong>${log.action || '任务'}</strong>
            <span class="badge bg-${statusClass} ms-2">${statusText}</span>
          </div>
          <p class="mb-0 text-muted" style="font-size: 0.9rem;">${log.message || ''}</p>
        </div>
        <small class="text-muted">${log.created_at || ''}</small>
      </div>
    `;
    container.appendChild(logItem);
  });
}

// 过滤运行中的日志：如果任务有成功或失败的日志，则隐藏运行中的日志
function filterRunningLogs(logs) {
  if (!logs || logs.length === 0) return logs;
  
  // 创建日志副本以避免修改原数组
  const logsToProcess = [...logs];
  const hasTerminalStatus = {}; // 记录每个任务是否有最终状态
  
  // 第一遍：找出所有有最终状态（成功/失败）的任务
  logsToProcess.forEach(log => {
    const taskKey = `${log.task_id || log.action}`;
    if (log.status === 'success' || log.status === 'failed') {
      hasTerminalStatus[taskKey] = true;
    }
  });
  
  // 第二遍：过滤掉有最终状态的任务的运行中日志
  return logsToProcess.filter(log => {
    const taskKey = `${log.task_id || log.action}`;
    if (log.status === 'running' && hasTerminalStatus[taskKey]) {
      return false; // 隐藏这个运行中的日志
    }
    return true; // 保留其他日志
  });
}

// 日志列表页
async function loadLogsPage() {
  document.getElementById('logFilterType').value = logsState.type;
  document.getElementById('logFilterLevel').value = logsState.level;
  document.getElementById('logFilterStatus').value = logsState.status;
  document.getElementById('logFilterKeyword').value = logsState.keyword;
  document.getElementById('logsPageSize').value = logsState.pageSize;
  await loadLogsData();
}

async function loadLogsData() {
  const list = document.getElementById('logsList');
  list.innerHTML = '<div class="text-center text-muted py-3">加载中...</div>';
  try {
    const data = await fetchLogs({
      type: logsState.type,
      level: logsState.level,
      status: logsState.status,
      keyword: logsState.keyword,
      page: logsState.page,
      page_size: logsState.pageSize
    });
    logsState.total = data.total || 0;
    renderLogsPageList(list, data.items || []);
    updateLogsPagination();
  } catch (error) {
    list.innerHTML = `<div class="text-center text-danger py-3">${error.message}</div>`;
  }
}

function renderLogsPageList(container, logs) {
  container.innerHTML = '';
  if (!logs || logs.length === 0) {
    container.innerHTML = '<div class="text-center text-muted py-3">暂无日志</div>';
    return;
  }
  logs.forEach(log => {
    const levelClass = logLevelClass(log.level);
    const badge = log.log_type === 'task' ? 'secondary' : levelClass;
    const statusText = log.status ? `<span class="badge bg-${badge} ms-2">${log.status}</span>` : '';
    const logItem = document.createElement('div');
    logItem.className = 'list-group-item list-group-item-action';
    logItem.innerHTML = `
      <div class="d-flex w-100 justify-content-between align-items-start">
        <div class="flex-grow-1">
          <div class="d-flex align-items-center mb-1">
            <span class="badge bg-${levelClass} me-2 text-uppercase">${(log.level || 'info')}</span>
            <strong class="me-2">${log.action || log.log_type || '日志'}</strong>
            ${statusText}
          </div>
          <div class="text-muted" style="font-size: 0.9rem;">${log.message || ''}</div>
          <div class="small text-muted mt-1">${log.username || '系统'} · ${log.log_type || ''}</div>
        </div>
        <small class="text-muted ms-2">${log.created_at || ''}</small>
      </div>
    `;
    container.appendChild(logItem);
  });
}

function updateLogsPagination() {
  const totalPages = Math.max(1, Math.ceil(logsState.total / logsState.pageSize));
  if (logsState.page > totalPages) {
    logsState.page = totalPages;
  }
  document.getElementById('logsSummary').textContent = `共 ${logsState.total} 条`;
  document.getElementById('logsPageInfo').textContent = `第 ${logsState.page} / ${totalPages} 页`;
}

function changeLogsPage(delta) {
  const totalPages = Math.max(1, Math.ceil(logsState.total / logsState.pageSize));
  const nextPage = logsState.page + delta;
  if (nextPage < 1 || nextPage > totalPages) return;
  logsState.page = nextPage;
  loadLogsData();
}

function onLogsPageSizeChange() {
  const size = parseInt(document.getElementById('logsPageSize').value, 10) || 10;
  logsState.pageSize = size;
  logsState.page = 1;
  loadLogsData();
}

function onLogsFilterChange() {
  logsState.type = document.getElementById('logFilterType').value;
  logsState.level = document.getElementById('logFilterLevel').value;
  logsState.status = document.getElementById('logFilterStatus').value;
  logsState.keyword = document.getElementById('logFilterKeyword').value.trim();
  logsState.page = 1;
  loadLogsData();
}

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
  loadDashboard();
});

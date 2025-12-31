"""
测试 IPTV 核心功能
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.tellyget_core import TellyGetCore


def test_tellyget_core():
    """测试 TellyGet 核心功能"""
    print("=" * 60)
    print("测试 IPTV 核心功能")
    print("=" * 60)
    
    # 注意：这里需要替换为真实的账号信息
    # 格式：
    # user: IPTV 账号（去掉 @iptv.gd 后缀）
    # passwd: IPTV 密码
    # mac: 机顶盒 MAC 地址
    
    print("\n请输入 IPTV 账号信息：")
    user = input("账号（不含 @iptv.gd）: ").strip()
    passwd = input("密码: ").strip()
    mac = input("MAC 地址（如 XX:D8:F3:73:09:YY）: ").strip()
    
    if not user or not passwd or not mac:
        print("\n❌ 错误：账号信息不完整")
        return
    
    print("\n正在测试...")
    print("-" * 60)
    
    # 创建核心实例
    core = TellyGetCore(
        user=user,
        passwd=passwd,
        mac=mac
    )
    
    # 获取频道
    success, result = core.fetch_channels(
        filter_sd=True,              # 过滤标清频道
        channel_filters=[r'^\d+$']   # 过滤纯数字频道名
    )
    
    if success:
        channels = result
        print(f"\n✅ 成功获取 {len(channels)} 个频道")
        print("-" * 60)
        
        # 显示前 10 个频道
        print("\n前 10 个频道：")
        for i, channel in enumerate(channels[:10], 1):
            info = TellyGetCore.parse_channel_info(channel)
            print(f"{i:2d}. {info['channel_name']}")
            print(f"    ID: {info['channel_id']}")
            print(f"    URL: {info['channel_url'][:60]}...")
            if info['channel_logo_url']:
                print(f"    Logo: {info['channel_logo_url'][:60]}...")
        
        # 显示统计信息
        print("\n" + "-" * 60)
        print("频道统计：")
        
        hd_count = sum(1 for ch in channels if '高清' in ch.get('ChannelName', ''))
        print(f"- 高清频道: {hd_count}")
        
        cctv_count = sum(1 for ch in channels if 'CCTV' in ch.get('ChannelName', ''))
        print(f"- CCTV 频道: {cctv_count}")
        
        satellite_count = sum(1 for ch in channels if '卫视' in ch.get('ChannelName', ''))
        print(f"- 卫视频道: {satellite_count}")
        
        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)
    else:
        print(f"\n❌ 失败：{result}")


if __name__ == '__main__':
    try:
        test_tellyget_core()
    except KeyboardInterrupt:
        print("\n\n测试已取消")
    except Exception as e:
        print(f"\n❌ 异常：{e}")
        import traceback
        traceback.print_exc()

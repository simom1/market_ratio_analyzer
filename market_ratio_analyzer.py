"""
市场比值分析工具
支持多种商品/货币对的比值分析
"""
import sys
from pathlib import Path

# 添加当前目录到路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from mt5_client.client import MT5Client, MT5Credentials
from mt5_client.periods import timeframe_from_str
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import matplotlib.dates as mdates

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# 预设的比值配置 - 主流实用比值
RATIO_PRESETS = {
    "金银比": {
        "symbol1": "XAUUSD",
        "symbol2": "XAGUSD",
        "name1": "黄金",
        "name2": "白银",
        "description": "经典避险金属比值，历史均值约80，投资者最关注"
    },
    "金铂比": {
        "symbol1": "XAUUSD",
        "symbol2": "XPTUSD",
        "name1": "黄金",
        "name2": "铂金",
        "description": "贵金属工业需求对比，铂金用于汽车催化剂和珠宝"
    },
    "油金比": {
        "symbol1": "XTIUSD",
        "symbol2": "XAUUSD",
        "name1": "原油",
        "name2": "黄金",
        "description": "经济活力指标，油价高说明经济强劲，金价高说明避险需求"
    },
    "纳指标普比": {
        "symbol1": "NAS100",
        "symbol2": "US500",
        "name1": "纳斯达克",
        "name2": "标普500",
        "description": "科技股vs大盘，比值高说明科技股强势"
    },
    "道指黄金比": {
        "symbol1": "US30",
        "symbol2": "XAUUSD",
        "name1": "道琼斯",
        "name2": "黄金",
        "description": "股市vs避险，比值高说明风险偏好强，低说明避险情绪浓"
    },
}

def get_historical_data(client: MT5Client, symbol: str, timeframe: int, days: int):
    """使用MT5Client获取历史数据"""
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    df = client.get_rates(
        symbol=symbol,
        timeframe=timeframe,
        from_time_utc=start_time,
        to_time_utc=end_time
    )
    
    print(f"✅ {symbol}: 获取 {len(df)} 条数据")
    return df

def calculate_ratio(df1, df2, name1, name2):
    """计算两个品种的比值"""
    # 重置索引以便合并
    df1_reset = df1.reset_index()
    df2_reset = df2.reset_index()
    
    # 合并数据
    merged = pd.merge(df1_reset[['time', 'close']], 
                      df2_reset[['time', 'close']], 
                      on='time', 
                      suffixes=(f'_{name1}', f'_{name2}'))
    
    # 计算比值
    merged['ratio'] = merged[f'close_{name1}'] / merged[f'close_{name2}']
    
    return merged

def plot_ratio_chart(data, ratio_name, name1, name2, description):
    """绘制比值曲线图"""
    fig, ax = plt.subplots(figsize=(16, 8))
    
    # 绘制曲线
    ax.plot(data['time'], data['ratio'], linewidth=1.5, color='#FFD700', label=f'{ratio_name}')
    
    # 添加均值线
    mean_ratio = data['ratio'].mean()
    ax.axhline(y=mean_ratio, color='red', linestyle='--', linewidth=1.5, 
               label=f'平均值: {mean_ratio:.2f}')
    
    # 添加标准差区间
    std_ratio = data['ratio'].std()
    ax.axhline(y=mean_ratio + std_ratio, color='orange', linestyle=':', linewidth=1, alpha=0.7)
    ax.axhline(y=mean_ratio - std_ratio, color='orange', linestyle=':', linewidth=1, alpha=0.7)
    ax.fill_between(data['time'], mean_ratio - std_ratio, mean_ratio + std_ratio, 
                     alpha=0.1, color='orange', label=f'±1标准差: {std_ratio:.2f}')
    
    # 添加±2标准差区间（浅色）
    ax.axhline(y=mean_ratio + 2*std_ratio, color='lightcoral', linestyle=':', linewidth=0.8, alpha=0.5)
    ax.axhline(y=mean_ratio - 2*std_ratio, color='lightcoral', linestyle=':', linewidth=0.8, alpha=0.5)
    ax.fill_between(data['time'], mean_ratio - 2*std_ratio, mean_ratio + 2*std_ratio, 
                     alpha=0.05, color='red')
    
    # 设置标题和标签
    days = (data['time'].iloc[-1] - data['time'].iloc[0]).days
    ax.set_title(f'{ratio_name}走势图 ({name1}/{name2})\n{description}', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('时间', fontsize=12)
    ax.set_ylabel(f'{ratio_name}', fontsize=12)
    
    # 格式化x轴日期
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    if days > 1000:
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
    elif days > 500:
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    else:
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    plt.xticks(rotation=45)
    
    # 添加网格
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # 添加图例
    ax.legend(loc='best', fontsize=10)
    
    # 计算当前相对位置
    current_ratio = data['ratio'].iloc[-1]
    percentile = (data['ratio'] < current_ratio).sum() / len(data) * 100
    
    # 添加统计信息
    stats_text = f'最新值: {current_ratio:.2f}\n'
    stats_text += f'分位数: {percentile:.1f}%\n'
    stats_text += f'最高值: {data["ratio"].max():.2f}\n'
    stats_text += f'最低值: {data["ratio"].min():.2f}\n'
    stats_text += f'数据点: {len(data)}\n'
    stats_text += f'时间跨度: {days}天'
    
    # 判断当前位置
    if current_ratio > mean_ratio + std_ratio:
        position = "偏高"
        color = 'lightcoral'
    elif current_ratio < mean_ratio - std_ratio:
        position = "偏低"
        color = 'lightgreen'
    else:
        position = "正常"
        color = 'wheat'
    
    stats_text += f'\n当前状态: {position}'
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
            fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor=color, alpha=0.6))
    
    plt.tight_layout()
    return fig

def analyze_ratio(ratio_key, timeframe_str="H4", days=1825):
    """分析指定的比值"""
    if ratio_key not in RATIO_PRESETS:
        print(f"❌ 未找到预设: {ratio_key}")
        print(f"可用预设: {', '.join(RATIO_PRESETS.keys())}")
        return
    
    config = RATIO_PRESETS[ratio_key]
    
    print("=" * 70)
    print(f"{ratio_key}分析工具")
    print("=" * 70)
    
    print(f"\n📊 分析配置:")
    print(f"   品种1: {config['symbol1']} ({config['name1']})")
    print(f"   品种2: {config['symbol2']} ({config['name2']})")
    print(f"   时间周期: {timeframe_str}")
    print(f"   数据范围: 最近{days}天")
    print(f"   说明: {config['description']}")
    print()
    
    try:
        timeframe = timeframe_from_str(timeframe_str)
        
        print("🔌 正在连接MT5...")
        with MT5Client(MT5Credentials()) as client:
            print("✅ MT5连接成功\n")
            
            # 获取数据
            print(f"📥 正在获取{config['name1']}数据...")
            df1 = get_historical_data(client, config['symbol1'], timeframe, days)
            
            print(f"📥 正在获取{config['name2']}数据...")
            df2 = get_historical_data(client, config['symbol2'], timeframe, days)
            
            # 计算比值
            print(f"\n🔢 正在计算{ratio_key}...")
            ratio_data = calculate_ratio(df1, df2, config['name1'], config['name2'])
            print(f"✅ 计算完成，共 {len(ratio_data)} 个数据点")
            
            # 显示统计信息
            current = ratio_data['ratio'].iloc[-1]
            mean = ratio_data['ratio'].mean()
            std = ratio_data['ratio'].std()
            percentile = (ratio_data['ratio'] < current).sum() / len(ratio_data) * 100
            
            print(f"\n📈 {ratio_key}统计:")
            print(f"   当前值: {current:.2f}")
            print(f"   平均值: {mean:.2f}")
            print(f"   标准差: {std:.2f}")
            print(f"   最高值: {ratio_data['ratio'].max():.2f} ({ratio_data.loc[ratio_data['ratio'].idxmax(), 'time'].strftime('%Y-%m-%d')})")
            print(f"   最低值: {ratio_data['ratio'].min():.2f} ({ratio_data.loc[ratio_data['ratio'].idxmin(), 'time'].strftime('%Y-%m-%d')})")
            print(f"   当前分位数: {percentile:.1f}%")
            
            # 判断当前位置
            if current > mean + std:
                print(f"   ⚠️  当前值偏高，{config['name1']}相对强势")
            elif current < mean - std:
                print(f"   ⚠️  当前值偏低，{config['name2']}相对强势")
            else:
                print(f"   ✅ 当前值在正常范围内")
            
            # 绘制图表
            print("\n🎨 正在生成图表...")
            fig = plot_ratio_chart(ratio_data, ratio_key, 
                                  config['name1'], config['name2'], 
                                  config['description'])
            
            # 保存文件
            safe_name = ratio_key.replace("/", "_")
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            filename = f"{safe_name}_{timestamp}.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"✅ 图表已保存: {filename}")
            
            csv_filename = f"{safe_name}_data_{timestamp}.csv"
            ratio_data.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            print(f"✅ 数据已保存: {csv_filename}")
            
            # 显示图表
            print("\n📊 正在显示图表...")
            plt.show()
        
        print("\n✅ 分析完成！")
        
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("\n可用的比值分析:")
    for i, (key, config) in enumerate(RATIO_PRESETS.items(), 1):
        print(f"{i}. {key}: {config['symbol1']}/{config['symbol2']} - {config['description']}")
    
    print("\n" + "="*70)
    choice = input("请选择要分析的比值 (输入数字或名称，直接回车默认分析金银比): ").strip()
    
    if not choice:
        ratio_key = "金银比"
    elif choice.isdigit():
        idx = int(choice) - 1
        keys = list(RATIO_PRESETS.keys())
        if 0 <= idx < len(keys):
            ratio_key = keys[idx]
        else:
            print("❌ 无效选择")
            return
    else:
        ratio_key = choice
    
    # 询问时间范围
    days_input = input("请输入时间范围(天数，直接回车默认5年=1825天): ").strip()
    days = int(days_input) if days_input.isdigit() else 1825
    
    # 询问时间周期
    timeframe_input = input("请输入时间周期(H1/H4/D1等，直接回车默认H4): ").strip().upper()
    timeframe_str = timeframe_input if timeframe_input else "H4"
    
    analyze_ratio(ratio_key, timeframe_str, days)

if __name__ == "__main__":
    main()

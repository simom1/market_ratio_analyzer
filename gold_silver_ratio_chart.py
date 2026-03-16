"""
金银比曲线图
使用4小时K线数据，展示最近2年的金银比走势
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

def get_historical_data(client: MT5Client, symbol: str, timeframe: int, days: int):
    """使用MT5Client获取历史数据"""
    # 计算起始时间
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    # 使用MT5Client获取数据
    df = client.get_rates(
        symbol=symbol,
        timeframe=timeframe,
        from_time_utc=start_time,
        to_time_utc=end_time
    )
    
    print(f"✅ {symbol}: 获取 {len(df)} 条数据")
    return df

def calculate_gold_silver_ratio(gold_df, silver_df):
    """计算金银比"""
    # MT5Client返回的DataFrame已经有time作为索引
    # 重置索引以便合并
    gold_reset = gold_df.reset_index()
    silver_reset = silver_df.reset_index()
    
    # 合并数据（使用时间对齐）
    merged = pd.merge(gold_reset[['time', 'close']], 
                      silver_reset[['time', 'close']], 
                      on='time', 
                      suffixes=('_gold', '_silver'))
    
    # 计算金银比
    merged['ratio'] = merged['close_gold'] / merged['close_silver']
    
    return merged

def plot_ratio_chart(data):
    """绘制金银比曲线图"""
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # 绘制曲线
    ax.plot(data['time'], data['ratio'], linewidth=1.5, color='#FFD700', label='金银比')
    
    # 添加均值线
    mean_ratio = data['ratio'].mean()
    ax.axhline(y=mean_ratio, color='red', linestyle='--', linewidth=1, 
               label=f'平均值: {mean_ratio:.2f}')
    
    # 添加标准差区间
    std_ratio = data['ratio'].std()
    ax.axhline(y=mean_ratio + std_ratio, color='orange', linestyle=':', linewidth=1, alpha=0.7)
    ax.axhline(y=mean_ratio - std_ratio, color='orange', linestyle=':', linewidth=1, alpha=0.7)
    ax.fill_between(data['time'], mean_ratio - std_ratio, mean_ratio + std_ratio, 
                     alpha=0.1, color='orange', label=f'±1标准差: {std_ratio:.2f}')
    
    # 设置标题和标签
    ax.set_title('金银比走势图 (最近5年, 4小时K线)', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('时间', fontsize=12)
    ax.set_ylabel('金银比', fontsize=12)
    
    # 格式化x轴日期
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))  # 5年数据，每4个月显示一次
    plt.xticks(rotation=45)
    
    # 添加网格
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # 添加图例
    ax.legend(loc='best', fontsize=10)
    
    # 添加统计信息
    stats_text = f'最新值: {data["ratio"].iloc[-1]:.2f}\n'
    stats_text += f'最高值: {data["ratio"].max():.2f}\n'
    stats_text += f'最低值: {data["ratio"].min():.2f}\n'
    stats_text += f'数据点: {len(data)}'
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
            fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    return fig

def main():
    """主函数"""
    print("=" * 60)
    print("金银比曲线图生成器")
    print("=" * 60)
    
    # 配置参数
    gold_symbol = "XAUUSD"  # 黄金
    silver_symbol = "XAGUSD"  # 白银
    timeframe_str = "H4"  # 4小时K线
    days = 1825  # 5年
    
    print(f"\n📊 数据配置:")
    print(f"   黄金品种: {gold_symbol}")
    print(f"   白银品种: {silver_symbol}")
    print(f"   时间周期: {timeframe_str}")
    print(f"   数据范围: 最近{days}天 (约5年)")
    print()
    
    try:
        # 获取时间周期常量
        timeframe = timeframe_from_str(timeframe_str)
        
        # 使用MT5Client
        print("🔌 正在连接MT5...")
        with MT5Client(MT5Credentials()) as client:
            print("✅ MT5连接成功")
            
            # 获取黄金数据
            print("\n📥 正在获取黄金数据...")
            gold_df = get_historical_data(client, gold_symbol, timeframe, days)
            
            # 获取白银数据
            print("📥 正在获取白银数据...")
            silver_df = get_historical_data(client, silver_symbol, timeframe, days)
            
            # 计算金银比
            print("\n🔢 正在计算金银比...")
            ratio_data = calculate_gold_silver_ratio(gold_df, silver_df)
            print(f"✅ 计算完成，共 {len(ratio_data)} 个数据点")
            
            # 显示统计信息
            print(f"\n📈 金银比统计:")
            print(f"   当前值: {ratio_data['ratio'].iloc[-1]:.2f}")
            print(f"   平均值: {ratio_data['ratio'].mean():.2f}")
            print(f"   最高值: {ratio_data['ratio'].max():.2f} ({ratio_data.loc[ratio_data['ratio'].idxmax(), 'time'].strftime('%Y-%m-%d')})")
            print(f"   最低值: {ratio_data['ratio'].min():.2f} ({ratio_data.loc[ratio_data['ratio'].idxmin(), 'time'].strftime('%Y-%m-%d')})")
            print(f"   标准差: {ratio_data['ratio'].std():.2f}")
            
            # 绘制图表
            print("\n🎨 正在生成图表...")
            fig = plot_ratio_chart(ratio_data)
            
            # 保存图表
            filename = f"gold_silver_ratio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"✅ 图表已保存: {filename}")
            
            # 保存数据到CSV
            csv_filename = f"gold_silver_ratio_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            ratio_data.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            print(f"✅ 数据已保存: {csv_filename}")
            
            # 显示图表
            print("\n📊 正在显示图表...")
            plt.show()
        
        print("\n✅ 完成！")
        
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

"""
批量分析所有主流市场比值
一次性生成所有比值的图表和数据
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

# 主流实用比值配置
RATIO_CONFIGS = [
    {
        "name": "金银比",
        "symbol1": "XAUUSD",
        "symbol2": "XAGUSD",
        "name1": "黄金",
        "name2": "白银",
        "description": "经典避险金属比值，历史均值约80，投资者最关注",
        "color": "#FFD700"
    },
    {
        "name": "金铂比",
        "symbol1": "XAUUSD",
        "symbol2": "XPTUSD",
        "name1": "黄金",
        "name2": "铂金",
        "description": "贵金属工业需求对比，铂金用于汽车催化剂和珠宝",
        "color": "#C0C0C0"
    },
    {
        "name": "油金比",
        "symbol1": "XTIUSD",
        "symbol2": "XAUUSD",
        "name1": "原油",
        "name2": "黄金",
        "description": "经济活力指标，油价高说明经济强劲，金价高说明避险需求",
        "color": "#8B4513"
    },
    {
        "name": "纳指标普比",
        "symbol1": "NAS100",
        "symbol2": "US500",
        "name1": "纳斯达克",
        "name2": "标普500",
        "description": "科技股vs大盘，比值高说明科技股强势",
        "color": "#4169E1"
    },
    {
        "name": "道指黄金比",
        "symbol1": "US30",
        "symbol2": "XAUUSD",
        "name1": "道琼斯",
        "name2": "黄金",
        "description": "股市vs避险，比值高说明风险偏好强，低说明避险情绪浓",
        "color": "#DC143C"
    },
]

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
    
    return df

def calculate_ratio(df1, df2):
    """计算两个品种的比值"""
    df1_reset = df1.reset_index()
    df2_reset = df2.reset_index()
    
    merged = pd.merge(df1_reset[['time', 'close']], 
                      df2_reset[['time', 'close']], 
                      on='time', 
                      suffixes=('_1', '_2'))
    
    merged['ratio'] = merged['close_1'] / merged['close_2']
    
    return merged

def plot_single_ratio(data, config):
    """绘制单个比值的独立图表"""
    fig, ax = plt.subplots(figsize=(16, 8))
    
    # 绘制曲线
    ax.plot(data['time'], data['ratio'], linewidth=2, color=config['color'], 
            label=config['name'], alpha=0.9)
    
    # 添加均值线
    mean_ratio = data['ratio'].mean()
    ax.axhline(y=mean_ratio, color='red', linestyle='--', linewidth=2, 
               label=f'均值: {mean_ratio:.2f}', alpha=0.8)
    
    # 添加标准差区间
    std_ratio = data['ratio'].std()
    ax.axhline(y=mean_ratio + std_ratio, color='orange', linestyle=':', linewidth=1.5, alpha=0.7)
    ax.axhline(y=mean_ratio - std_ratio, color='orange', linestyle=':', linewidth=1.5, alpha=0.7)
    ax.fill_between(data['time'], mean_ratio - std_ratio, mean_ratio + std_ratio, 
                     alpha=0.15, color='orange', label=f'±1标准差: {std_ratio:.2f}')
    
    # 添加±2标准差区间
    ax.axhline(y=mean_ratio + 2*std_ratio, color='lightcoral', linestyle=':', linewidth=1, alpha=0.5)
    ax.axhline(y=mean_ratio - 2*std_ratio, color='lightcoral', linestyle=':', linewidth=1, alpha=0.5)
    ax.fill_between(data['time'], mean_ratio - 2*std_ratio, mean_ratio + 2*std_ratio, 
                     alpha=0.08, color='red')
    
    # 设置标题
    days = (data['time'].iloc[-1] - data['time'].iloc[0]).days
    ax.set_title(f'{config["name"]}走势图 ({config["name1"]}/{config["name2"]})\n{config["description"]}', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('时间', fontsize=12)
    ax.set_ylabel(config['name'], fontsize=12)
    
    # 格式化x轴
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # 网格
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
    
    # 图例
    ax.legend(loc='best', fontsize=11)
    
    # 计算当前状态
    current = data['ratio'].iloc[-1]
    percentile = (data['ratio'] < current).sum() / len(data) * 100
    max_val = data['ratio'].max()
    min_val = data['ratio'].min()
    
    # 状态标注
    if current > mean_ratio + std_ratio:
        status = "偏高"
        color = 'lightcoral'
    elif current < mean_ratio - std_ratio:
        status = "偏低"
        color = 'lightgreen'
    else:
        status = "正常"
        color = 'wheat'
    
    # 添加统计信息
    stats_text = f'最新值: {current:.2f}\n'
    stats_text += f'分位数: {percentile:.1f}%\n'
    stats_text += f'最高值: {max_val:.2f}\n'
    stats_text += f'最低值: {min_val:.2f}\n'
    stats_text += f'数据点: {len(data)}\n'
    stats_text += f'时间跨度: {days}天\n'
    stats_text += f'当前状态: {status}'
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
            fontsize=11, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor=color, alpha=0.7, edgecolor='black', linewidth=1.5))
    
    plt.tight_layout()
    return fig

def create_summary_table(all_results):
    """创建汇总表格"""
    summary_data = []
    
    for result in all_results:
        config = result['config']
        data = result['data']
        
        current = data['ratio'].iloc[-1]
        mean = data['ratio'].mean()
        std = data['ratio'].std()
        percentile = (data['ratio'] < current).sum() / len(data) * 100
        
        # 判断状态
        if current > mean + std:
            status = "偏高 ⬆️"
            interpretation = f"{config['name1']}相对强势"
        elif current < mean - std:
            status = "偏低 ⬇️"
            interpretation = f"{config['name2']}相对强势"
        else:
            status = "正常 ➡️"
            interpretation = "均衡状态"
        
        summary_data.append({
            '比值': config['name'],
            '当前值': f"{current:.2f}",
            '均值': f"{mean:.2f}",
            '标准差': f"{std:.2f}",
            '分位数': f"{percentile:.0f}%",
            '状态': status,
            '解读': interpretation
        })
    
    return pd.DataFrame(summary_data)

def main():
    """主函数"""
    print("=" * 80)
    print("批量市场比值分析")
    print("=" * 80)
    
    timeframe_str = "H4"
    days = 1825  # 5年
    
    print(f"\n📊 分析配置:")
    print(f"   时间周期: {timeframe_str}")
    print(f"   数据范围: 最近{days}天 (约5年)")
    print(f"   分析数量: {len(RATIO_CONFIGS)}个比值")
    print()
    
    try:
        timeframe = timeframe_from_str(timeframe_str)
        
        print("🔌 正在连接MT5...")
        with MT5Client(MT5Credentials()) as client:
            print("✅ MT5连接成功\n")
            
            all_results = []
            
            # 逐个分析
            for i, config in enumerate(RATIO_CONFIGS, 1):
                print(f"\n{'='*80}")
                print(f"[{i}/{len(RATIO_CONFIGS)}] 分析 {config['name']}")
                print(f"{'='*80}")
                print(f"说明: {config['description']}")
                
                # 获取数据
                print(f"\n📥 获取{config['name1']}数据 ({config['symbol1']})...", end=" ")
                df1 = get_historical_data(client, config['symbol1'], timeframe, days)
                print(f"✅ {len(df1)}条")
                
                print(f"📥 获取{config['name2']}数据 ({config['symbol2']})...", end=" ")
                df2 = get_historical_data(client, config['symbol2'], timeframe, days)
                print(f"✅ {len(df2)}条")
                
                # 计算比值
                print(f"🔢 计算{config['name']}...", end=" ")
                ratio_data = calculate_ratio(df1, df2)
                print(f"✅ {len(ratio_data)}个数据点")
                
                # 统计信息
                current = ratio_data['ratio'].iloc[-1]
                mean = ratio_data['ratio'].mean()
                std = ratio_data['ratio'].std()
                max_val = ratio_data['ratio'].max()
                min_val = ratio_data['ratio'].min()
                percentile = (ratio_data['ratio'] < current).sum() / len(ratio_data) * 100
                
                print(f"\n📈 统计:")
                print(f"   当前值: {current:.2f}")
                print(f"   平均值: {mean:.2f}")
                print(f"   标准差: {std:.2f}")
                print(f"   最高值: {max_val:.2f}")
                print(f"   最低值: {min_val:.2f}")
                print(f"   分位数: {percentile:.1f}%")
                
                if current > mean + std:
                    print(f"   ⚠️  当前偏高，{config['name1']}相对强势")
                elif current < mean - std:
                    print(f"   ⚠️  当前偏低，{config['name2']}相对强势")
                else:
                    print(f"   ✅ 当前在正常范围")
                
                all_results.append({
                    'config': config,
                    'data': ratio_data
                })
            
            # 创建独立图表
            print(f"\n\n{'='*80}")
            print("🎨 生成图表...")
            print(f"{'='*80}\n")
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            for result in all_results:
                config = result['config']
                data = result['data']
                
                print(f"📊 生成{config['name']}图表...", end=" ")
                
                # 生成独立图表
                fig = plot_single_ratio(data, config)
                
                # 保存图表
                filename = f"{config['name']}_{timestamp}.png"
                plt.savefig(filename, dpi=300, bbox_inches='tight')
                plt.close(fig)  # 关闭图表，释放内存
                
                print(f"✅ {filename}")
            
            # 保存各个比值的数据
            print(f"\n💾 保存数据文件...")
            for result in all_results:
                config = result['config']
                data = result['data']
                csv_filename = f"{config['name']}_data_{timestamp}.csv"
                data.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                print(f"✅ {csv_filename}")
            
            # 创建汇总表格
            print(f"\n{'='*80}")
            print("📋 汇总报告")
            print(f"{'='*80}\n")
            
            summary_df = create_summary_table(all_results)
            print(summary_df.to_string(index=False))
            
            # 保存汇总表格
            summary_filename = f"市场比值汇总_{timestamp}.csv"
            summary_df.to_csv(summary_filename, index=False, encoding='utf-8-sig')
            print(f"\n✅ 汇总表格已保存: {summary_filename}")
            
            print("\n✅ 所有分析完成！")
            print(f"\n📁 生成的文件:")
            print(f"   - 5个独立图表 (PNG)")
            print(f"   - 5个数据文件 (CSV)")
            print(f"   - 1个汇总报告 (CSV)")
            
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

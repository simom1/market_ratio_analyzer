"""
检查MT5平台上各品种的4小时数据可用性
"""
import sys
from pathlib import Path

# 添加当前目录到路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from mt5_client.client import MT5Client, MT5Credentials
from mt5_client.periods import timeframe_from_str
from datetime import datetime, timedelta
import MetaTrader5 as mt5

# 常见的交易品种列表
SYMBOLS_TO_CHECK = {
    "贵金属": [
        "XAUUSD",  # 黄金
        "XAGUSD",  # 白银
        "XPTUSD",  # 铂金
        "XPDUSD",  # 钯金
    ],
    "主要货币对": [
        "EURUSD",  # 欧美
        "GBPUSD",  # 镑美
        "USDJPY",  # 美日
        "USDCHF",  # 美瑞
        "AUDUSD",  # 澳美
        "NZDUSD",  # 纽美
        "USDCAD",  # 美加
    ],
    "交叉货币对": [
        "EURJPY",  # 欧日
        "GBPJPY",  # 镑日
        "EURGBP",  # 欧镑
        "AUDJPY",  # 澳日
        "EURAUD",  # 欧澳
        "AUDNZD",  # 澳纽
    ],
    "能源": [
        "XTIUSD",  # WTI原油
        "XBRUSD",  # 布伦特原油
        "XNGUSD",  # 天然气
    ],
    "指数": [
        "US30",    # 道琼斯
        "US500",   # 标普500
        "NAS100",  # 纳斯达克
        "GER40",   # 德国DAX
        "UK100",   # 英国富时
        "JPN225",  # 日经225
    ],
}

def check_symbol_data(client: MT5Client, symbol: str, timeframe: int, days: int):
    """检查单个品种的数据可用性"""
    try:
        # 先检查品种是否存在
        info = mt5.symbol_info(symbol)
        if info is None:
            return {
                "symbol": symbol,
                "available": False,
                "reason": "品种不存在",
                "bars": 0,
                "start_date": None,
                "end_date": None,
                "days_span": 0
            }
        
        # 尝试获取数据
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        df = client.get_rates(
            symbol=symbol,
            timeframe=timeframe,
            from_time_utc=start_time,
            to_time_utc=end_time
        )
        
        if len(df) == 0:
            return {
                "symbol": symbol,
                "available": False,
                "reason": "无数据",
                "bars": 0,
                "start_date": None,
                "end_date": None,
                "days_span": 0
            }
        
        # 计算实际时间跨度
        actual_start = df.index[0]
        actual_end = df.index[-1]
        days_span = (actual_end - actual_start).days
        
        return {
            "symbol": symbol,
            "available": True,
            "reason": "数据完整",
            "bars": len(df),
            "start_date": actual_start.strftime('%Y-%m-%d'),
            "end_date": actual_end.strftime('%Y-%m-%d'),
            "days_span": days_span
        }
        
    except Exception as e:
        return {
            "symbol": symbol,
            "available": False,
            "reason": str(e)[:50],
            "bars": 0,
            "start_date": None,
            "end_date": None,
            "days_span": 0
        }

def main():
    """主函数"""
    print("=" * 80)
    print("MT5平台4小时数据可用性检查")
    print("=" * 80)
    
    timeframe_str = "H4"
    days = 1825  # 检查5年数据
    
    print(f"\n检查配置:")
    print(f"  时间周期: {timeframe_str}")
    print(f"  检查范围: 最近{days}天 (约5年)")
    print()
    
    try:
        timeframe = timeframe_from_str(timeframe_str)
        
        print("🔌 正在连接MT5...")
        with MT5Client(MT5Credentials()) as client:
            print("✅ MT5连接成功\n")
            
            all_results = {}
            
            # 遍历所有类别
            for category, symbols in SYMBOLS_TO_CHECK.items():
                print(f"\n{'='*80}")
                print(f"📊 {category}")
                print(f"{'='*80}")
                
                results = []
                for symbol in symbols:
                    print(f"检查 {symbol}...", end=" ")
                    result = check_symbol_data(client, symbol, timeframe, days)
                    results.append(result)
                    
                    if result["available"]:
                        print(f"✅ {result['bars']}条 ({result['start_date']} ~ {result['end_date']}, {result['days_span']}天)")
                    else:
                        print(f"❌ {result['reason']}")
                
                all_results[category] = results
            
            # 生成汇总报告
            print(f"\n\n{'='*80}")
            print("📋 汇总报告")
            print(f"{'='*80}\n")
            
            for category, results in all_results.items():
                available = [r for r in results if r["available"]]
                unavailable = [r for r in results if not r["available"]]
                
                print(f"\n{category}:")
                print(f"  ✅ 可用: {len(available)}/{len(results)}")
                
                if available:
                    avg_bars = sum(r["bars"] for r in available) / len(available)
                    avg_days = sum(r["days_span"] for r in available) / len(available)
                    print(f"  📊 平均数据量: {avg_bars:.0f}条 ({avg_days:.0f}天)")
                    print(f"  📈 可用品种: {', '.join(r['symbol'] for r in available)}")
                
                if unavailable:
                    print(f"  ❌ 不可用: {', '.join(r['symbol'] for r in unavailable)}")
            
            # 推荐的比值对
            print(f"\n\n{'='*80}")
            print("💡 推荐的比值分析对")
            print(f"{'='*80}\n")
            
            # 检查贵金属比值
            metals = all_results.get("贵金属", [])
            metals_available = {r["symbol"]: r for r in metals if r["available"]}
            
            if "XAUUSD" in metals_available and "XAGUSD" in metals_available:
                print("✅ 金银比 (XAUUSD/XAGUSD) - 经典避险金属比值")
            
            if "XAUUSD" in metals_available and "XPTUSD" in metals_available:
                print("✅ 金铂比 (XAUUSD/XPTUSD) - 贵金属工业需求对比")
            
            if "XAUUSD" in metals_available and "XPDUSD" in metals_available:
                print("✅ 金钯比 (XAUUSD/XPDUSD) - 汽车工业相关")
            
            # 检查货币对比值
            currencies = all_results.get("主要货币对", [])
            currencies_available = {r["symbol"]: r for r in currencies if r["available"]}
            
            if "EURUSD" in currencies_available and "GBPUSD" in currencies_available:
                print("✅ 欧美/镑美比 (EURUSD/GBPUSD) - 欧洲货币强弱")
            
            if "AUDUSD" in currencies_available and "NZDUSD" in currencies_available:
                print("✅ 澳美/纽美比 (AUDUSD/NZDUSD) - 商品货币对比")
            
            # 检查能源和黄金比值
            energy = all_results.get("能源", [])
            energy_available = {r["symbol"]: r for r in energy if r["available"]}
            
            if "XTIUSD" in energy_available and "XAUUSD" in metals_available:
                print("✅ 油金比 (XTIUSD/XAUUSD) - 经济活力指标")
            
            # 检查指数比值
            indices = all_results.get("指数", [])
            indices_available = {r["symbol"]: r for r in indices if r["available"]}
            
            if "NAS100" in indices_available and "US500" in indices_available:
                print("✅ 纳指/标普比 (NAS100/US500) - 科技股vs大盘")
            
            if "US30" in indices_available and "XAUUSD" in metals_available:
                print("✅ 道指/黄金比 (US30/XAUUSD) - 股市vs避险")
            
            print("\n✅ 检查完成！")
            
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

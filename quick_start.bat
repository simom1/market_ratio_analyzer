@echo off
chcp 65001 >nul
echo ========================================
echo 市场比值分析工具 - 快速开始
echo ========================================
echo.

:menu
echo 请选择要执行的操作:
echo.
echo 1. 检查数据可用性
echo 2. 批量分析所有比值（推荐）
echo 3. 单独分析金银比
echo 4. 交互式分析
echo 5. 安装依赖
echo 0. 退出
echo.
set /p choice=请输入选项 (0-5): 

if "%choice%"=="1" goto check_data
if "%choice%"=="2" goto analyze_all
if "%choice%"=="3" goto gold_silver
if "%choice%"=="4" goto interactive
if "%choice%"=="5" goto install
if "%choice%"=="0" goto end
echo 无效选项，请重新选择
goto menu

:check_data
echo.
echo 正在检查数据可用性...
python check_h4_data_availability.py
pause
goto menu

:analyze_all
echo.
echo 正在批量分析所有比值...
python analyze_all_ratios.py
pause
goto menu

:gold_silver
echo.
echo 正在分析金银比...
python gold_silver_ratio_chart.py
pause
goto menu

:interactive
echo.
echo 启动交互式分析...
python market_ratio_analyzer.py
pause
goto menu

:install
echo.
echo 正在安装依赖...
pip install -r requirements.txt
echo.
echo 安装完成！
pause
goto menu

:end
echo.
echo 感谢使用！
exit

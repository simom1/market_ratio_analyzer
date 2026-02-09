@echo off
chcp 65001 >nul
echo ========================================
echo 推送到GitHub
echo ========================================
echo.

cd /d %~dp0

echo 检查Git状态...
git status
echo.

echo 添加所有文件...
git add .
echo.

echo 提交更改...
set /p commit_msg=请输入提交信息 (直接回车使用默认): 
if "%commit_msg%"=="" set commit_msg=Update: 更新市场比值分析

git commit -m "%commit_msg%"
echo.

echo 推送到GitHub...
git push -u origin main
echo.

if %errorlevel% equ 0 (
    echo ✅ 推送成功！
    echo.
    echo 访问你的仓库: https://github.com/simom1/market_ratio_analyzer
) else (
    echo ❌ 推送失败
    echo.
    echo 可能的原因:
    echo 1. 需要配置GitHub认证
    echo 2. 网络连接问题
    echo 3. 仓库权限问题
    echo.
    echo 请尝试手动执行:
    echo git push -u origin main
)

echo.
pause

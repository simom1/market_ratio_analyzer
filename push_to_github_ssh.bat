@echo off
chcp 65001 >nul
echo ========================================
echo 使用SSH推送到GitHub
echo ========================================
echo.

cd /d %~dp0

echo 步骤1: 检查当前远程地址
git remote -v
echo.

echo 步骤2: 切换到SSH地址
git remote set-url origin git@github.com:simom1/market_ratio_analyzer.git
echo ✅ 已切换到SSH地址
echo.

echo 步骤3: 验证SSH连接
echo 测试SSH连接...
ssh -T git@github.com
echo.

echo 步骤4: 添加并提交更改
git add .
set /p commit_msg=请输入提交信息 (直接回车使用默认): 
if "%commit_msg%"=="" set commit_msg=Update: 更新市场比值分析

git commit -m "%commit_msg%"
echo.

echo 步骤5: 推送到GitHub
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ✅ 推送成功！
    echo 访问: https://github.com/simom1/market_ratio_analyzer
) else (
    echo.
    echo ❌ 推送失败
    echo.
    echo 如果提示权限问题，请先配置SSH密钥:
    echo 1. 生成密钥: ssh-keygen -t ed25519 -C "your_email@example.com"
    echo 2. 复制公钥: type %USERPROFILE%\.ssh\id_ed25519.pub
    echo 3. 添加到GitHub: https://github.com/settings/keys
)

echo.
pause

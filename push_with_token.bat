@echo off
chcp 65001 >nul
echo ========================================
echo 使用Personal Access Token推送到GitHub
echo ========================================
echo.

cd /d %~dp0

echo 如果还没有Personal Access Token，请先创建:
echo 1. 访问: https://github.com/settings/tokens
echo 2. 点击 "Generate new token" - "Generate new token (classic)"
echo 3. 勾选 "repo" 权限
echo 4. 生成并复制token
echo.

echo 步骤1: 切换回HTTPS地址
git remote set-url origin https://github.com/simom1/market_ratio_analyzer.git
echo ✅ 已切换到HTTPS地址
echo.

echo 步骤2: 添加并提交更改
git add .

set /p commit_msg=请输入提交信息 (直接回车使用默认): 
if "%commit_msg%"=="" set commit_msg=Update: 更新市场比值分析

git commit -m "%commit_msg%"
echo.

echo 步骤3: 推送到GitHub
echo.
echo ⚠️ 重要提示:
echo 当提示输入密码时，请输入你的Personal Access Token（不是GitHub密码）
echo.
pause

git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo ✅ 推送成功！
    echo ========================================
    echo.
    echo 访问你的仓库:
    echo https://github.com/simom1/market_ratio_analyzer
    echo.
    echo 💡 提示: 为了避免每次都输入token，可以使用:
    echo git config --global credential.helper store
    echo 下次推送后会自动保存凭据
) else (
    echo.
    echo ❌ 推送失败
    echo.
    echo 请确保:
    echo 1. 已创建Personal Access Token
    echo 2. Token有repo权限
    echo 3. 输入的是token而不是密码
)

echo.
pause

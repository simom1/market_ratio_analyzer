@echo off
chcp 65001 >nul
echo ========================================
echo Git 初始化和配置
echo ========================================
echo.

cd /d %~dp0

echo 步骤1: 初始化Git仓库
git init
echo.

echo 步骤2: 配置Git用户信息（如果还没配置）
echo 当前Git配置:
git config user.name
git config user.email
echo.

set /p setup_user=是否需要配置Git用户信息? (y/n): 
if /i "%setup_user%"=="y" (
    set /p git_name=请输入你的GitHub用户名: 
    set /p git_email=请输入你的GitHub邮箱: 
    git config user.name "!git_name!"
    git config user.email "!git_email!"
    echo ✅ 用户信息配置完成
    echo.
)

echo 步骤3: 添加所有文件
git add .
echo ✅ 文件已添加
echo.

echo 步骤4: 首次提交
git commit -m "Initial commit: Market Ratio Analyzer v1.0.0"
echo ✅ 提交完成
echo.

echo 步骤5: 设置主分支为main
git branch -M main
echo ✅ 分支设置完成
echo.

echo 步骤6: 添加远程仓库
git remote add origin https://github.com/simom1/market_ratio_analyzer.git
echo ✅ 远程仓库已添加
echo.

echo 步骤7: 推送到GitHub
echo 正在推送...
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo ✅ 成功推送到GitHub！
    echo ========================================
    echo.
    echo 访问你的仓库:
    echo https://github.com/simom1/market_ratio_analyzer
    echo.
) else (
    echo.
    echo ========================================
    echo ⚠️ 推送失败
    echo ========================================
    echo.
    echo 可能需要配置GitHub认证:
    echo.
    echo 方法1: 使用GitHub Desktop
    echo   - 下载并安装GitHub Desktop
    echo   - 登录你的GitHub账号
    echo   - 然后重新运行此脚本
    echo.
    echo 方法2: 使用Personal Access Token
    echo   1. 访问 https://github.com/settings/tokens
    echo   2. 生成新的token（勾选repo权限）
    echo   3. 使用token作为密码推送
    echo.
    echo 方法3: 使用SSH密钥
    echo   1. 生成SSH密钥: ssh-keygen -t ed25519 -C "your_email@example.com"
    echo   2. 添加到GitHub: https://github.com/settings/keys
    echo   3. 修改远程地址: git remote set-url origin git@github.com:simom1/market_ratio_analyzer.git
    echo.
)

echo.
pause

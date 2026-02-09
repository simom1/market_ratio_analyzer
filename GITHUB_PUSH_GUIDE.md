# GitHub推送指南

## 问题诊断

你遇到的问题是SSH密钥权限不足。当前使用的SSH密钥是deploy key，只有读取权限，没有写入权限。

## 解决方案

### 方案1: 使用Personal Access Token（推荐）

这是最简单的方法：

#### 步骤1: 创建Personal Access Token

1. 访问 https://github.com/settings/tokens
2. 点击 **"Generate new token"** → **"Generate new token (classic)"**
3. 设置token名称，如 "market_ratio_analyzer"
4. 勾选权限：
   - ✅ **repo** (完整的仓库访问权限)
5. 点击 **"Generate token"**
6. **立即复制token**（只显示一次！）

#### 步骤2: 使用token推送

运行脚本：
```bash
push_with_token.bat
```

当提示输入密码时，粘贴你的Personal Access Token（不是GitHub密码）。

#### 步骤3: 保存凭据（可选）

为了避免每次都输入token，运行：
```bash
git config --global credential.helper store
```

下次推送后会自动保存凭据。

---

### 方案2: 添加新的SSH密钥（个人账户）

如果你想继续使用SSH：

#### 步骤1: 生成新的SSH密钥

```bash
ssh-keygen -t ed25519 -C "your_email@example.com" -f ~/.ssh/id_ed25519_personal
```

#### 步骤2: 添加到SSH agent

```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519_personal
```

#### 步骤3: 复制公钥

```bash
type %USERPROFILE%\.ssh\id_ed25519_personal.pub
```

#### 步骤4: 添加到GitHub

1. 访问 https://github.com/settings/keys
2. 点击 **"New SSH key"**
3. 标题: "Personal Key - Market Ratio Analyzer"
4. 粘贴公钥内容
5. 点击 **"Add SSH key"**

#### 步骤5: 配置SSH使用新密钥

编辑 `~/.ssh/config`:
```
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_personal
```

#### 步骤6: 推送

```bash
git push -u origin main
```

---

### 方案3: 使用GitHub Desktop（最简单）

1. 下载并安装 [GitHub Desktop](https://desktop.github.com/)
2. 登录你的GitHub账号
3. 在GitHub Desktop中打开 `market_ratio_analysis` 文件夹
4. 点击 **"Publish repository"**
5. 完成！

---

### 方案4: 使用GitHub CLI

#### 安装GitHub CLI

下载: https://cli.github.com/

#### 认证

```bash
gh auth login
```

选择：
- GitHub.com
- HTTPS
- 使用浏览器登录

#### 推送

```bash
cd market_ratio_analysis
git push -u origin main
```

---

## 当前状态

你的本地仓库已经配置好了：
- ✅ Git仓库已初始化
- ✅ 文件已提交
- ✅ 远程仓库已添加
- ⚠️ 只需要解决认证问题

## 推荐方案

**对于Windows用户，我推荐使用方案1（Personal Access Token）**，因为：
- 最简单，不需要配置SSH
- 可以设置过期时间，更安全
- 可以随时撤销
- 支持credential helper自动保存

## 快速操作

1. 创建token: https://github.com/settings/tokens
2. 运行: `push_with_token.bat`
3. 输入token作为密码
4. 完成！

---

## 常见问题

### Q: Token和密码有什么区别？
A: GitHub已经不再支持使用密码推送代码，必须使用Personal Access Token。

### Q: Token会过期吗？
A: 可以设置过期时间，也可以设置为永不过期。

### Q: 如果忘记token怎么办？
A: 无法找回，只能重新生成一个新的token。

### Q: 可以同时使用多个token吗？
A: 可以，每个token可以设置不同的权限和过期时间。

---

## 联系支持

如果还有问题，可以：
1. 查看GitHub文档: https://docs.github.com/
2. 提交Issue到本仓库
3. 联系GitHub支持

---

**祝你推送成功！** 🚀

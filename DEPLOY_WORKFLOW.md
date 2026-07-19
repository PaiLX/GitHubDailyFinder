# GitHub Daily Finder 本地迭代与上线流程

> 这份文档可以提交到 GitHub；不要在这里写 token、API key 等敏感信息。敏感信息只放本地 `.private/deploy-config.local.md`。

## 目标

每次后续修改产品时，按同一套流程完成：

```text
本地修改功能
→ 本地验证
→ 提交代码
→ 更新 GitHub 仓库
→ GitHub Pages 自动发布
→ 自定义域名可访问
→ 每日定时任务继续自动拉取/AI归类
```

## 固定项目信息

- 本地项目目录：`E:\Hermes_agent_folder\AdRevenueTool_2026-07-01\GitHubDailyFinder`
- GitHub 仓库：`https://github.com/PaiLX/GitHubDailyFinder`
- 线上域名：`https://dailyopensources.bbroot.com/`
- GitHub Pages 源：`main` 分支 `/` 根目录
- 每日数据任务：`.github/workflows/daily-update.yml`
- 数据更新脚本：`scripts/update_data.py`
- 广告配置：`js/ad-config.js`

## 敏感信息存放规则

不要提交以下内容：

- GitHub Token
- AI API Key
- 其他平台密钥
- 本地临时脚本

本项目已在 `.gitignore` 忽略：

```text
.private/
.env
.env.*
```

敏感信息只放：

```text
.private/deploy-config.local.md
```

## 每次迭代标准流程

### 1. 修改功能

常见文件：

```text
index.html
css/style.css
js/app.js
js/ad-config.js
scripts/update_data.py
.github/workflows/daily-update.yml
```

### 2. 本地验证

在项目目录运行：

```bash
python -m py_compile scripts/update_data.py fetch_data.py generate_combined.py
curl -s -o /dev/null -w 'HTTP:%{http_code}\n' http://localhost:8080/
```

如果本地服务没开，可运行：

```bash
python -m http.server 8080
```

然后访问：

```text
http://localhost:8080/
```

### 3. 检查 Git 状态

```bash
git status --short
```

确认没有把 `.private/`、`.env`、token 文件、临时文件加入提交。

### 4. 本地提交

```bash
git add .
git commit -m "feat: 描述本次修改"
```

### 5. 推送到 GitHub

优先使用 GitHub Desktop：

```text
打开 GitHub Desktop
→ 选择 GitHubDailyFinder 仓库
→ 确认变更
→ Push origin
```

如果命令行网络正常，也可以：

```bash
git push origin main
```

本机曾出现过 Git 代理 `127.0.0.1:7890` 导致 push 失败；如果命令行失败，直接用 GitHub Desktop 更省事。

### 6. 等待 GitHub Pages 发布

推送后 GitHub Pages 会自动部署。

查看位置：

```text
GitHub 仓库 → Actions → pages build and deployment
```

成功状态应为：

```text
completed success
```

### 7. 检查线上网站

访问：

```text
https://dailyopensources.bbroot.com/
```

需要确认：

- 页面能打开
- 样式正常
- 项目卡片正常加载
- 搜索/筛选正常
- 联系弹窗正常
- 广告位未破坏布局

## 每日数据更新流程

工作流：

```text
.github/workflows/daily-update.yml
```

默认每天北京时间 09:00 运行。

手动触发位置：

```text
GitHub 仓库 → Actions → Daily GitHub Data Update → Run workflow
```

成功后会更新：

```text
data/combined.json
data/translations_v2.json
data/update_report.json
```

## GitHub Secrets

当前工作流依赖以下 GitHub Secrets：

```text
AI_API_KEY
AI_BASE_URL
AI_MODEL
```

位置：

```text
GitHub 仓库 → Settings → Secrets and variables → Actions
```

如果 AI key 更换，只需要更新这里，不要写入代码。

## 广告配置

广告文件：

```text
js/ad-config.js
```

可提交的信息：

- Publisher ID
- 广告 slot ID

不要提交广告后台登录信息。

## DNS 配置

域名：

```text
dailyopensources.bbroot.com
```

DNS 需要配置：

```text
类型：CNAME
主机记录：@
记录值：pailx.github.io
TTL：自动
```

如果在上级域名 `bbroot.com` 管理面板配置，则通常是：

```text
类型：CNAME
主机记录：dailyopensources
记录值：pailx.github.io
```

不要修改 NS 服务器，保持 DNS 服务商默认即可。

## 常见故障

### 1. 域名打不开

检查：

```bash
nslookup dailyopensources.bbroot.com
```

应指向 GitHub Pages 相关地址。DNS 刚保存可能需要等待几分钟到数小时。

### 2. GitHub Pages 没更新

检查：

```text
GitHub → Actions → pages build and deployment
```

看是否成功。

### 3. 每日数据没更新

检查：

```text
GitHub → Actions → Daily GitHub Data Update
```

如果失败，优先看：

- AI Secrets 是否正确
- GitHub API 是否限流
- `scripts/update_data.py` 是否有语法错误

### 4. 广告不显示

可能原因：

- AdSense 审核未通过
- 域名未在 AdSense 站点列表通过
- 广告单元 slot ID 不正确
- 广告被浏览器插件拦截
- 新广告位需要等待一段时间才开始填充

## 给 Hermes 的下次执行摘要

当用户说“更新 GitHub Daily Finder 并上线”时，按这个顺序：

1. 读取本文件和 `.private/deploy-config.local.md`
2. 修改本地文件
3. 本地验证 HTTP 200 和关键功能
4. `git status` 检查敏感文件未加入
5. 提交代码
6. 优先让用户/GitHub Desktop push；如 token 可用则 API 或 git push
7. 检查 GitHub Actions Pages 构建成功
8. 检查 `https://dailyopensources.bbroot.com/`
9. 简短汇报：改了什么、验证结果、线上地址

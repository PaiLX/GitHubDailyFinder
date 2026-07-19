# GitHub Daily Finder

面向中文用户的 GitHub 开源项目发现站。

## 功能

- 四个父级角色分类：开发工具、设计创意、产品运营、测试安全
- 每个父级分类保留 20 个项目池
- 角色关注点子分类动态变化
- 中文名称、中文描述、项目作用、核心价值
- GitHub 下载方式说明
- 联系方式弹窗
- 广告位预留与 AdSense 加载脚本
- GitHub Actions 每天 09:00 自动更新数据

## 本地预览

```bash
python -m http.server 8080
```

访问：

```text
http://localhost:8080/
```

## 自动更新配置

GitHub Actions 需要以下 Secrets：

```text
AI_API_KEY
AI_BASE_URL
AI_MODEL
```

可选：

```text
GH_DATA_TOKEN
```

如果不设置 `GH_DATA_TOKEN`，工作流会使用 GitHub Actions 自带的 `github.token`。

## 广告配置

广告配置文件：

```text
js/ad-config.js
```

已填 Publisher ID：

```text
ca-pub-7512053198282052
```

如果需要让固定广告位真实填充，还需要在 AdSense 后台创建广告单元并填写：

```js
slots: {
  top: '顶部广告单元ID',
  side: '侧边广告单元ID',
  bottom: '底部广告单元ID'
}
```

## 部署建议

免费方案优先级：

1. GitHub Pages：完全免费，最简单
2. Cloudflare Pages：免费，速度好
3. Vercel：免费额度够用，但需要绑定账号

当前项目已经包含 GitHub Actions 定时更新，可配合 GitHub Pages 使用。

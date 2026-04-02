# X Daily Watch 🐦

> 关注 X (Twitter) 大V，每日自动抓取推文推送，长文备份到飞书文档。

[![免登录](https://img.shields.io/badge/免登录-无需X账号-brightgreen)](https://github.com/openclaw/openclaw)
[![免梯子](https://img.shields.io/badge/免梯子-国内直接访问-brightgreen)](https://github.com/openclaw/openclaw)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenClaw](https://img.shields.io/badge/Powered%20by-OpenClaw-blue)](https://github.com/openclaw/openclaw)

> ✅ **无需 X/Twitter 账号** · ✅ **无需翻墙** · ✅ **国内网络直接可用**

## ✨ 功能特性

- **🔓 免登录访问** - 无需 X/Twitter 账号，无需 API Key，开箱即用
- **🌐 国内可用** - 无需梯子，国内网络环境直接访问
- **🔄 自动抓取** - 每天 5:55 AM 自动抓取关注用户 24 小时内的最新推文
- **📊 热度筛选** - 按 likes + retweets 排序，每用户最多推送 5 条
- **📝 完整内容** - 包含推文全文和转发原文
- **📄 长文备份** - 超过 500 字自动备份到飞书文档
- **💬 飞书推送** - 消息直接发送到飞书，附带文档链接
- **🗣️ 对话管理** - 通过自然语言添加/移除关注用户

## 📦 安装

### 前置要求

- OpenClaw 运行环境
- Python 3.8+
- 飞书开放平台应用

### 快速开始

1. **克隆到 OpenClaw skills 目录**

```bash
cd ~/.openclaw/workspace/skills
git clone https://github.com/your-username/x-daily-watch.git
```

2. **创建数据目录**

```bash
mkdir -p ~/.openclaw/workspace/data/x-daily-watch
```

3. **初始化配置文件**

```bash
cat > ~/.openclaw/workspace/data/x-daily-watch/config.json << 'EOF'
{
  "users": [],
  "backup_config": {
    "enabled": true,
    "min_length": 500
  }
}
EOF
```

4. **配置飞书应用**

在 `~/.openclaw/openclaw.json` 中配置飞书渠道：

```json
{
  "channels": {
    "feishu": {
      "enabled": true,
      "appId": "cli_your_app_id",
      "appSecret": "your_app_secret",
      "dmPolicy": "allowlist",
      "allowFrom": ["ou_your_user_id"]
    }
  }
}
```

5. **测试运行**

```bash
cd ~/.openclaw/workspace/skills/x-daily-watch/scripts
python3 fetch_and_push.py
```

## ⚙️ 配置

### 飞书权限

在 [飞书开放平台](https://open.feishu.cn/app/) 添加以下权限：

| 权限 | 用途 |
|------|------|
| `docx:document` | 读取文档 |
| `docx:document:create` | 创建文档 |
| `im:message` | 发送消息 |

### 定时任务

使用 OpenClaw cron 配置每日推送：

```bash
openclaw cron add --name "x-daily-watch-push" \
  --schedule "55 5 * * *" \
  --timezone "Asia/Shanghai" \
  --command "cd ~/.openclaw/workspace/skills/x-daily-watch/scripts && python3 fetch_and_push.py"
```

## 🚀 使用方法

### 对话指令

| 指令 | 功能 |
|------|------|
| `帮我关注 @username` | 添加用户到关注列表 |
| `帮我关注 @username 别名` | 添加用户并设置别名 |
| `取消关注 @username` | 移除用户 |
| `查看关注列表` | 显示所有关注用户 |
| `手动抓取一次推文` | 立即执行抓取和推送 |

### 示例

```
用户: 帮我关注 @elonmusk Elon Musk
助手: ✅ 已添加 @elonmusk (Elon Musk) 到关注列表！

用户: 查看关注列表
助手:
当前关注列表 (3 人):
| 用户 | 别名 |
|------|------|
| @LufzzLiz | 岚叔 |
| @dotey | 宝玉 |
| @elonmusk | Elon Musk |
```

## 📁 目录结构

```
~/.openclaw/workspace/
├── skills/x-daily-watch/          # 技能目录
│   ├── SKILL.md                   # OpenClaw 操作指南
│   ├── README.md                  # 本文档
│   └── scripts/                   # 脚本目录
│       ├── config_manager.py      # 配置管理
│       ├── twitter_client.py      # Twitter API 客户端
│       ├── feishu_doc.py          # 飞书推送模块
│       └── fetch_and_push.py      # 主执行脚本
│
└── data/x-daily-watch/            # 数据目录
    ├── config.json                # 关注列表配置
    ├── history.json               # 历史记录
    ├── push_message.md            # 最新推送消息
    └── stats.json                 # 执行统计
```

## 🔧 配置文件

### config.json

```json
{
  "users": [
    {
      "username": "elonmusk",
      "alias": "Elon Musk",
      "added_at": "2026-04-01",
      "max_tweets": 5
    }
  ],
  "backup_config": {
    "enabled": true,
    "min_length": 500
  }
}
```

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `username` | X 用户名 | 必填 |
| `alias` | 显示别名 | username |
| `max_tweets` | 每用户最多推送条数 | 5 |
| `min_length` | 长文字数阈值 | 500 |

## 📤 推送格式

```markdown
# X 每日追踪 - 2026-04-01 05:55

## Elon Musk

Starship is go for launch! 🚀

❤️ 150000 | 🔁 25000
🔗 https://twitter.com/elonmusk/status/xxx

---

📄 **长文备份文档**: https://open.feishu.cn/docx/xxx
共 3 篇长文
```

## 🛠️ 技术栈

| 组件 | 技术 |
|------|------|
| 数据源 | vxtwitter API, fxtwitter RSS |
| 推送渠道 | 飞书开放 API |
| 定时任务 | OpenClaw cron |
| 运行时 | Python 3 |

## ❓ 常见问题

### 飞书配置未找到

**错误**: `飞书配置未找到，请在 ~/.openclaw/openclaw.json 配置 channels.feishu`

**解决**: 确保 `~/.openclaw/openclaw.json` 包含飞书配置，且 `enabled: true`

### 飞书文档无法访问

**原因**: 文档创建后未授权给用户

**解决**: 在飞书开放平台添加 `drive:drive` 权限

### 推文获取失败

**可能原因**:
- vxtwitter API 限流
- 用户名不存在或账号被封
- 网络问题

**排查**:
```bash
curl "https://api.vxtwitter.com/elonmusk"
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📄 许可证

[MIT License](LICENSE)

## 🙏 致谢

- [vxtwitter](https://github.com/dylanpdx/vxtwitter) - Twitter API 代理
- [fxtwitter](https://github.com/FixTweet/FxTwitter) - Twitter RSS 服务
- [OpenClaw](https://github.com/openclaw/openclaw) - AI Agent 框架

---

**⭐ 如果这个项目对你有帮助，请给个 Star！**